from data_processing.get_tiers import main as get_tiers
from data_processing.get_unrestricted_learnsets import main as get_unrestricted_learnsets
from data_processing.get_learnsets import main as get_learnsets

if __name__ == "__main__":
    print("Fetching and processing tier data...")
    get_tiers()
    print("Fetching and processing unrestricted learnsets...")
    get_unrestricted_learnsets()
    print("Processing tier learnsets...")
    get_learnsets()
    print("Data processing complete.")