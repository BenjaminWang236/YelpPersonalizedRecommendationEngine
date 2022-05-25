from collections import defaultdict
import json
import os
from pathlib import Path
import requests as req
import pandas as pd
import surprise
from surprise import Dataset, Reader, BaselineOnly, dump
from surprise.model_selection import train_test_split
import mysql.connector
from mysql.connector import errorcode
from flask import Flask,jsonify,request

app = Flask(__name__, static_folder='static')


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
    """Yunyan's SQL connection code snippet from test.py. Modified for Reviews query.

    Returns:
        pd.DataFrame: df with user_id, business_id, stars from Yelp Reviews table
    """
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


def load_settings(
    recommender_settings_file: Path = "recommender_settings.json",
) -> list:
    """Load in the Surprise recommender settings from a JSON file.

    Args:
        recommender_settings_file (Path, optional): file-path to setting. Defaults to "recommender_settings.json".

    Returns:
        list: all 7 settings in a list
    """
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
        print(f"Saving default recommender settings to {recommender_settings_file}")
        with open(recommender_settings_file, "w") as f:
            json.dump(setting_dict, f)
    with open(recommender_settings_file, "r") as f:
        setting_dict = json.load(f)
    ret = [
        setting_dict["use_prev_top_n"],
        setting_dict["use_prev_predictions"],
        setting_dict["use_prev_trained_model"],
        setting_dict["load_from_dataframe"],
        setting_dict["num_to_recommend"],
        setting_dict["file_path"],
        setting_dict["algo_progress_dir"],
    ]
    return ret


def preparation(algo_progress_dir: str = "./algo_checkpoints/") -> list:
    """Prepare the algorithm, with optimal parameters, and the filenames to saved intermediate results.

    Args:
        algo_progress_dir (str, optional): internal directory. Defaults to "./algo_checkpoints/".

    Returns:
        list: algorithm for recommender, and all filenames used internally
    """
    # Best algo for both RMSE and runtime: BaselineOnly(). Using best parameter found in limited gridSearch
    ret = [
        BaselineOnly(
            bsl_options={
                "method": "sgd",
                "reg": 0.02,
                "learning_rate": 0.01,
                "n_epochs": 20,
            }
        )
    ]
    algo_name = str(ret[0].__class__.__name__)
    ret.append(f"{algo_progress_dir}algo_final_serialize_{algo_name}")
    ret.append(f"{algo_progress_dir}predictions_final_serialize_{algo_name}")
    ret.append(f"{algo_progress_dir}top_n_final_json_{algo_name}.json")
    ret.append(f"{algo_progress_dir}top_n_iid_final_json_{algo_name}.json")
    ret.append(f"{algo_progress_dir}testset_final_json_{algo_name}.json")
    return ret

@app.route('/sampleurl', methods = ['POST'])
def samplefunction():
    #access your DB get your results here
    user = request.args.get('nm')
    data = {"data":user}
    "return jsonify(data)"
    return user

@app.route('/recommend', methods = ['POST'])
def main():
    [
        use_prev_top_n,
        use_prev_predictions,
        use_prev_trained_model,
        load_from_dataframe,
        num_to_recommend,
        file_path,
        algo_progress_dir,
    ] = load_settings()
    [
        algo,
        file_name,
        pred_name,
        top_n_name,
        top_n_iid_name,
        testset_name,
    ] = preparation(algo_progress_dir)

    """
    In final version, we will only train (fit) the recommendation 
    algorithm once, save it, then use it to make predictions
    for ALL users in the testset all at once each time the database 
    is updated. Save the predictions, then use them to make recommendations.
    Save the recommendations, then use them to respond to user requests.
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

    """
    # debug print-outs: Comment out in final version
    from more_itertools import take

    # n_items = take(num_to_recommend, top_n.items())
    n_items_iid_only = take(num_to_recommend, top_n_iid_only.items())
    # print(f"Top {num_to_recommend} recommendations for each user:\n{n_items}")
    print(f"Top {num_to_recommend} recommendations for each user (iid only):\n")
    import pprint as pp

    # pp.pprint(n_items)
    pp.pprint(n_items_iid_only)
    """

    """
    # Request-handler for test-user-ids
    # Note: The test-users are in testset, saved to testset_name file in algo_checkpoints dir.
    #       Format of testset JSON file is [[uid, bid, stars], [uid, bid, stars], ...]
    #       Extract the uid out of each test-user-id, remove duplicates, and that's the list of users
    #       to send to the frontend.
    with open(testset_name, "r") as f:
        testset_reloaded = json.load(f)
    testset_uid_only = [uid for (uid, _, _) in testset_reloaded]
    testset_uid_only = list(set(testset_uid_only))  # Removing duplicates
    """

    user_list = request.args.get('user')
    #take input from user list

    # res = list(top_n_iid_only.keys())[0]


    # Request-handler for returning list of business_id recommendations for specified testset user
    #       top_n_iid_only is the dictionary of top-n recommendations for all testset users.
    # print(top_n_iid_only["kF6HYfuRDv-yAj4W8aGqbA"])   # How to access the dictionary for specific user
    # Returns "[['ReX09lhufLTAx19krkltDA', 'C_uHOxo1zIJaQuzAY6JvxQ']]", bussiness_id list
    recommend_list = top_n_iid_only[user_list]
    ans = ' '.join(str(v) for v in recommend_list)
    return json.dumps(recommend_list)

@app.route('/searchuser', methods = ['GET'])
def searchuser():
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
    user_search = request.args.get('user')
    q = "SELECT * FROM Users WHERE uid='{0}'".format(user_search)
    cursor = cnx.cursor()
    cursor.execute(q)
    row=cursor.fetchone()
    if(row):
        return json.dumps(row, indent=4, sort_keys=True, default=str)
    else:
        return "Record Not Found!"


@app.route('/searchbusiness', methods = ['GET'])
def searchbusiness():
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
    business_search = request.args.get('business')
    q="Select * from Businesses where bid='{0}'".format(business_search)
    cursor = cnx.cursor()
    cursor.execute(q)
    row=cursor.fetchone()
    if(row):
        return json.dumps(row, indent=4, sort_keys=True, default=str)
    else:
        return "Record Not Found!"

@app.route('/reviews', methods = ['GET'])
def reviews():
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
    business_search = request.args.get('business')
    q="Select content from Reviews where bid='{0}'".format(business_search)
    cursor = cnx.cursor()
    cursor.execute(q)
    row=cursor.fetchone()
    if(row):
        return json.dumps(row, indent=4, sort_keys=True, default=str)
    else:
        return "Record Not Found!"

@app.route('/getphoto', methods = ['GET'])
def getphoto():
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
    business_search = request.args.get('business')
    q="Select pid from Photos where bid='{0}'".format(business_search)
    cursor = cnx.cursor()
    cursor.execute(q)
    row=cursor.fetchone()
    if(row):
        return json.dumps(row, indent=4, sort_keys=True, default=str)
    else:
        return "Record Not Found!"

from flask import current_app,send_from_directory

@app.route('/uploads/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    uploads = os.path.join(current_app.root_path, 'Photos/photos/')
    print(uploads)
    return send_from_directory(directory=uploads, filename=filename)


if __name__ == "__main__":
    port = 8000
    app.run(host='0.0.0.0',port=port)
