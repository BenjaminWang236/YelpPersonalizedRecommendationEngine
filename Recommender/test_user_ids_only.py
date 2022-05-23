import json

def main():
    testset_name = "testset_final_json_BaselineOnly.json"
    test_users_only_name = "test_users_only.json"
    with open(testset_name, "r") as f:
        testset_reloaded = json.load(f)
    testset_uid_only = [uid for (uid, _, _) in testset_reloaded]
    testset_uid_only = list(set(testset_uid_only))  # Removing duplicates
    with open(test_users_only_name, "w") as f:
        json.dump(testset_uid_only, f)

if __name__ == '__main__':
    main()
