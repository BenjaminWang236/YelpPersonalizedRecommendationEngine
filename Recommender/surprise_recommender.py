from collections import defaultdict
import json
from pathlib import Path
import requests as req
import pandas as pd
import surprise
from surprise import Dataset, Reader, BaselineOnly, dump
from surprise.model_selection import train_test_split
import mysql.connector
from mysql.connector import errorcode


def get_top_n(predictions, n=10) -> defaultdict:
    """Return the top-N recommendation for each user from a set of predictions.
    From Surprise's examples/top_n_recommendations.py

    Args:
        predictions(list of Prediction objects): The list of predictions, as
            returned by the test method of an algorithm.
        n(int): The number of recommendation to output for each user. Default
            is 10.

    Returns:
    A dict where keys are user (raw) ids and values are lists of tuples:
        [(raw item id, rating estimation), ...] of size n.
    """

    # First map the predictions to each user.
    top_n = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        top_n[uid].append((iid, est))

    # Then sort the predictions for each user and retrieve the k highest ones.
    for uid, user_ratings in top_n.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_n[uid] = user_ratings[:n]

    return top_n


def read_sql_into_dataframe() -> pd.DataFrame:
    try:
        cnx = mysql.connector.connect(
            user="admin",
            password="606HaoYunLai606!",
            port="3306",
            host="database-1.c50spqkkfz7j.us-west-1.rds.amazonaws.com",
            database="db",
        )
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
        exit()
    print("Successfully connected to the database")
    # cursor = cnx.cursor()
    query = "SELECT uid, bid, stars FROM Reviews"
    # cursor.execute(query)
    df = pd.read_sql_query(query, cnx)
    print("Closing the connection and cursor...")
    # cursor.close()
    cnx.close()
    return df


def main():
    # If database not updated, and have trained model/predictions, load it
    recommender_settings_file = "recommender_settings.json"
    path = Path(recommender_settings_file)
    if not path.is_file():
        setting_dict = {
            "use_prev_top_n": True,
            "use_prev_trained_model": False,
            "use_prev_predictions": False,
            "load_from_dataframe": False,
            "num_to_recommend": 10,
            "file_path": "yelp_reviews.csv",
            "algo_progress_dir": "./algo_checkpoints/",
        }
        print(f"Save recommender settings to {recommender_settings_file}")
        with open(recommender_settings_file, "w") as f:
            json.dump(setting_dict, f)
    with open(recommender_settings_file, "r") as f:
        setting_dict = json.load(f)
    use_prev_top_n = setting_dict["use_prev_top_n"]
    use_prev_predictions = setting_dict["use_prev_predictions"]
    use_prev_trained_model = setting_dict["use_prev_trained_model"]
    load_from_dataframe = setting_dict["load_from_dataframe"]
    num_to_recommend = setting_dict["num_to_recommend"]
    file_path = setting_dict["file_path"]
    algo_progress_dir = setting_dict["algo_progress_dir"]

    # Best algo for both RMSE and runtime: BaselineOnly(). Using best parameter found in limited gridSearch
    algo = BaselineOnly(
        bsl_options={
            "method": "sgd",
            "reg": 0.02,
            "learning_rate": 0.01,
            "n_epochs": 20,
        }
    )
    file_name = (
        f"{algo_progress_dir}algo_final_serialize_{str(algo.__class__.__name__)}"
    )
    pred_name = (
        f"{algo_progress_dir}predictions_final_serialize_{str(algo.__class__.__name__)}"
    )
    top_n_name = (
        f"{algo_progress_dir}top_n_final_json_{str(algo.__class__.__name__)}.json"
    )
    top_n_iid_name = (
        f"{algo_progress_dir}top_n_iid_final_json_{str(algo.__class__.__name__)}.json"
    )
    testset_name = (
        f"{algo_progress_dir}testset_final_json_{str(algo.__class__.__name__)}.json"
    )

    """
    In final version, we will only train (fit) the recommendation 
    algorithm once, save it, then use it to make predictions
    for ALL users in the testset all at once each time the database 
    is updated. Save the predictions, then use them to make recommendations.
    Save the recommendations, the use them to respond to user requests.
    """
    if use_prev_top_n:
        with open(top_n_name, "r") as f:
            top_n = json.load(f)
        with open(top_n_iid_name, "r") as f:
            top_n_iid_only = json.load(f)
    else:
        if use_prev_predictions:
            predictions, _ = dump.load(pred_name)
        else:
            # Import the dataset & prepare it
            reader = Reader(
                line_format="user item rating",
                sep=",",
                skip_lines=1,
                rating_scale=(1, 5),
            )
            if not load_from_dataframe:
                data = Dataset.load_from_file(file_path=file_path, reader=reader)
            else:
                df = read_sql_into_dataframe()
                data = Dataset.load_from_df(df=df, reader=reader)
            trainset, testset = train_test_split(data, test_size=0.25)
            with open(testset_name, "w") as f:
                json.dump(testset, f)
            if use_prev_trained_model:
                _, algo = dump.load(file_name)
            else:
                algo.fit(trainset)
                dump.dump(file_name, algo=algo, verbose=1)
                use_prev_trained_model = True
            predictions = algo.test(testset)
            dump.dump(pred_name, predictions=predictions, verbose=1)
            use_prev_predictions = True
            # print(predictions[0:10])
        top_n = get_top_n(predictions, n=num_to_recommend)
        with open(top_n_name, "w") as f:
            json.dump(top_n, f)
        top_n_iid_only = defaultdict(list)
        for uid, user_ratings in top_n.items():
            top_n_iid_only[uid].append([iid for (iid, _) in user_ratings])
            # print(uid, [iid for (iid, _) in user_ratings])
        with open(top_n_iid_name, "w") as f:
            json.dump(top_n_iid_only, f)
        use_prev_top_n = True

    # debug print-outs: Comment out in final version
    from more_itertools import take

    # n_items = take(num_to_recommend, top_n.items())
    n_items_iid_only = take(num_to_recommend, top_n_iid_only.items())
    # print(f"Top {num_to_recommend} recommendations for each user:\n{n_items}")
    print(f"Top {num_to_recommend} recommendations for each user (iid only):\n")
    import pprint as pp

    # pp.pprint(n_items)
    pp.pprint(n_items_iid_only)

    # TODO: Request-handler for test-user-ids
    # Note: The test-users are in testset, saved to testset_name file in algo_checkpoints dir.
    #       Format of testset JSON file is [[uid, bid, stars], [uid, bid, stars], ...]
    #       Extract the uid out of each test-user-id, remove duplicates, and that's the list of users
    #       to send to the frontend.
    with open(testset_name, "r") as f:
        testset_reloaded = json.load(f)
    testset_uid_only = [uid for (uid, _, _) in testset_reloaded]
    testset_uid_only = list(set(testset_uid_only))  # Removing duplicates

    # TODO: Request-handler for returning list of business_id recommendations for specified testset user
    #       top_n_iid_only is the dictionary of top-n recommendations for all testset users.
    # print(top_n_iid_only["kF6HYfuRDv-yAj4W8aGqbA"])   # How to access the dictionary for specific user
    # Returns "[['ReX09lhufLTAx19krkltDA', 'C_uHOxo1zIJaQuzAY6JvxQ']]", bussiness_id list


if __name__ == "__main__":
    main()
