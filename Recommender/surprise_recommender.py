import surprise
from surprise import Dataset, Reader, SVD, accuracy, SVDpp, NMF, NormalPredictor, BaselineOnly, CoClustering
from surprise.model_selection import cross_validate, train_test_split, GridSearchCV
import pandas as pd
import pprint as pp
from collections import defaultdict
from surprise import dump

def get_top_n(predictions, n=10):
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

def main():
    # Import the dataset & prepare it
    file_path = 'yelp_reviews.csv'
    algo_progress_dir = '.\\algo_checkpoints\\'
    reader = Reader(line_format='user item rating', sep=',', skip_lines=1, rating_scale=(1, 5))
    data = Dataset.load_from_file(file_path=file_path, reader=reader)
    trainset, testset = train_test_split(data, test_size=.25)
    
    # Best algo for both RMSE and runtime: BaselineOnly(). Using best parameter find in limited gridSearch
    param = {'bsl_options': {'method': 'sgd', 'reg': 0.02, 'learning_rate': 0.01, 'n_epochs': 20}}
    algo = BaselineOnly(bsl_options=param['bsl_options'])
    algo.fit(trainset)
    predictions = algo.test(testset)
    # check predicitons
    print(predictions[0:10])
    
    # Save/Deump the algorithm
    file_name = f"{algo_progress_dir}algo_test_serialize_{str(algo.__class__.__name__)}"
    dump.dump(file_name, algo=algo)
    # Reload the dumped/saved algorithm
    _, loaded_algo = dump.load(file_name)
    
    # Check the reloaded algo is the same as the original
    predictions_loaded = loaded_algo.test(testset)
    assert predictions == predictions_loaded
    print(f"Predictions match!")
    
    top_n = get_top_n(predictions, n=10)
    # Print the recommended items for each user
    num_to_print, curr_num = 10, 0
    for uid, user_ratings in top_n.items():
        if curr_num >= num_to_print:
            break
        print(uid, [iid for (iid, _) in user_ratings])
        curr_num += 1
    
if __name__ == '__main__':
    main()