import json
import os
from re import sub
import matplotlib.pyplot as plt
from collections import Counter

OUTPUT_DIR = "output/"

PROFILES = "jsons/profiles.json"
GENIUSES = "jsons/geniuses.json"
GENIUS_PAIRS = "jsons/genius_pairs.json"

with open(GENIUSES, "r", encoding="utf-8") as f:
    geniuses = json.load(f)

with open(PROFILES, "r", encoding="utf-8") as f:
    profiles = json.load(f)

with open(GENIUS_PAIRS, "r", encoding="utf-8") as f:
    genius_pairs = json.load(f)


FILTERS = {
    "has_role",
    "team",
    "chair",
    "active",
    "inactive",
    "no_role",
    "active_team",
    "active_chair",
    "inactive_team",
    "inactive_chair",
    "male",
    "female",
    "male_role",
    "female_role",
    "theology_branch",
    "bible_study_branch",
    "community_outreach_branch"
}


def should_filter_profile(profile, filter):
    """
    Determine if a profile should be filtered based on the provided filter.
    """
    if filter is None:
        return False

    if filter == "has_role":
        return not profile.get("role")
    elif filter == "team":
        return profile.get("role") != "team"
    elif filter == "chair":
        return profile.get("role") != "chair"
    elif filter == "active":
        return not profile.get("active", False)
    elif filter == "inactive":
        return profile.get("active", True)
    elif filter == "no_role":
        return profile.get("role") is not None
    elif filter == "active_team":
        return not (profile.get("active", False) and profile.get("role") == "team")
    elif filter == "active_chair":
        return not (profile.get("active", False) and profile.get("role") == "chair")
    elif filter == "inactive_team":
        return not (not profile.get("active", True) and profile.get("role") == "team")
    elif filter == "inactive_chair":
        return not (not profile.get("active", True) and profile.get("role") == "chair")
    elif filter == "male":
        return not profile.get("male", False)
    elif filter == "female":
        return profile.get("male", True)
    elif filter == "male_role":
        return not (profile.get("male", False) and profile.get("role") is not None)
    elif filter == "female_role":
        return not (not profile.get("male", True) and profile  .get("role") is not None)
    elif filter == "theology_branch":
        return profile.get("branch") != "Theology on Tap"
    elif filter == "bible_study_branch":
        return profile.get("branch") != "Bible Study"
    elif filter == "community_outreach_branch":
        return profile.get("branch") != "Community Outreach"
    else:
        raise ValueError(f"Unknown filter: {filter}")


def plot_genius_distribution(filter=None):
    """
    Plot the distribution of geniuses by their field of expertise.
    """

    genius_counts = {genius_name: 0 for genius_name in geniuses.keys()}

    for name, profile in profiles.items():
        if should_filter_profile(profile, filter):
            continue
        print(f"Analyzing profile: {name}")
        for genius_name in geniuses.keys():
            if genius_name in profile['genius']:
                genius_counts[genius_name] += 1

    plt.figure(figsize=(10, 6))
    plt.bar(genius_counts.keys(), genius_counts.values(), color='green')
    plt.xlabel('Genius Name')
    plt.ylabel('Number of Profiles')
    plt.title('Distribution of Geniuses by Number of Profiles')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}genius_distribution.png')
    plt.show()


def plot_genius_distribution(filter=None, subdir=""):
    """
    Plot the distribution of geniuses by their field of expertise.
    """

    genius_counts = {genius_name: {"either": 0, "first": 0, "second": 0}
                     for genius_name in geniuses.keys()}
    profile_count = 0

    for name, profile in profiles.items():
        if should_filter_profile(profile, filter):
            continue
        print(f"Analyzing profile: {name}")
        for genius_name in geniuses.keys():
            if genius_name in profile['genius']:
                genius_counts[genius_name]["either"] += 1
            if genius_name == profile['genius'][0]:
                genius_counts[genius_name]["first"] += 1
            if genius_name == profile['genius'][1]:
                genius_counts[genius_name]["second"] += 1
        profile_count += 1

    for pos in ["either", "first", "second"]:
        counts = {genius_name: genius_counts[genius_name][pos]
                  for genius_name in genius_counts}
        plt.figure(figsize=(10, 6))
        plt.bar(counts.keys(), counts.values(), color='green')
        plt.xlabel('Genius Name')
        plt.ylabel('Number of Profiles')
        plt.title(
            f'Distribution of Geniuses by Number of Profiles ({profile_count}) - {pos}: {filter if filter else "All"}')
        plt.xticks(rotation=45)
        plt.tight_layout()
        os.makedirs(f'{OUTPUT_DIR}{subdir}{pos}', exist_ok=True)
        plt.savefig(f'{OUTPUT_DIR}{subdir}{pos}/genius_distribution_{pos}.png')


def plot_competency_distribution(filter=None, subdir=""):
    """
    Plot the distribution of competencies by their field of expertise.
    """

    competency_counts = {genius_name: {"either": 0, "first": 0, "second": 0}
                         for genius_name in geniuses.keys()}
    profile_count = 0

    for name, profile in profiles.items():
        if should_filter_profile(profile, filter):
            continue
        print(f"Analyzing profile: {name}")

        for genius_name in geniuses.keys():
            if genius_name in profile['competency']:
                competency_counts[genius_name]["either"] += 1

            if genius_name == profile['competency'][0]:
                competency_counts[genius_name]["first"] += 1

            if genius_name == profile['competency'][1]:
                competency_counts[genius_name]["second"] += 1

        profile_count += 1

    for pos in ["either", "first", "second"]:
        counts = {genius_name: competency_counts[genius_name][pos]
                  for genius_name in competency_counts}

        plt.figure(figsize=(10, 6))
        plt.bar(counts.keys(), counts.values(), color='orange')
        plt.xlabel('Competency Name')
        plt.ylabel('Number of Profiles')
        plt.title(
            f'Distribution of Competencies by Number of Profiles ({profile_count}) - {pos}: {filter if filter else "All"}'
        )
        plt.xticks(rotation=45)
        plt.tight_layout()

        os.makedirs(f'{OUTPUT_DIR}{subdir}{pos}', exist_ok=True)
        plt.savefig(
            f'{OUTPUT_DIR}{subdir}{pos}/competency_distribution_{pos}.png'
        )
        plt.close()


def plot_frustration_distribution(filter=None, subdir=""):
    """
    Plot the distribution of frustrations by their field of expertise.
    """

    frustration_counts = {genius_name: {"either": 0, "first": 0, "second": 0}
                          for genius_name in geniuses.keys()}
    profile_count = 0

    for name, profile in profiles.items():
        if should_filter_profile(profile, filter):
            continue
        print(f"Analyzing profile: {name}")

        for genius_name in geniuses.keys():
            if genius_name in profile['frustration']:
                frustration_counts[genius_name]["either"] += 1

            if genius_name == profile['frustration'][0]:
                frustration_counts[genius_name]["first"] += 1

            if genius_name == profile['frustration'][1]:
                frustration_counts[genius_name]["second"] += 1

        profile_count += 1

    for pos in ["either", "first", "second"]:
        counts = {genius_name: frustration_counts[genius_name][pos]
                  for genius_name in frustration_counts}

        plt.figure(figsize=(10, 6))
        plt.bar(counts.keys(), counts.values(), color='red')
        plt.xlabel('Frustration Name')
        plt.ylabel('Number of Profiles')
        plt.title(
            f'Distribution of Frustrations by Number of Profiles ({profile_count}) - {pos}: {filter if filter else "All"}'
        )
        plt.xticks(rotation=45)
        plt.tight_layout()

        os.makedirs(f'{OUTPUT_DIR}{subdir}{pos}', exist_ok=True)
        plt.savefig(
            f'{OUTPUT_DIR}{subdir}{pos}/frustration_distribution_{pos}.png'
        )
        plt.close()


def write_filter_summary(filter, subdir=""):
    """
    Write a summary of the number of profiles that match the given filter.
    """
    profile_count = 0
    for name, profile in profiles.items():
        if should_filter_profile(profile, filter):
            continue
        profile_count += 1

    with open(f'{OUTPUT_DIR}{subdir}names.txt', 'w') as f:
        f.write(f'Filter: {filter if filter else "All"}\n')
        f.write(f'Number of Profiles: {profile_count}\n')
        f.write('Profiles:\n')
        for name, profile in profiles.items():
            if should_filter_profile(profile, filter):
                continue
            f.write(f'- {name}\n')


plot_genius_distribution(subdir="all/")
plot_competency_distribution(subdir="all/")
plot_frustration_distribution(subdir="all/")

write_filter_summary(filter=None)

for filter in FILTERS:
    print(f"Plotting genius distribution with filter: {filter}")
    plot_genius_distribution(filter=filter, subdir=f"filtered/{filter}/")
    print(f"Plotting competency distribution with filter: {filter}")
    plot_competency_distribution(filter=filter, subdir=f"filtered/{filter}/")
    print(f"Plotting frustration distribution with filter: {filter}")
    plot_frustration_distribution(filter=filter, subdir=f"filtered/{filter}/")
    write_filter_summary(filter, subdir=f"filtered/{filter}/")
