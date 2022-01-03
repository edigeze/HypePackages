import jk_pypiorgapi
from datetime import datetime
import re
import requests
import time
from pprint import pprint
import json
import pickle
from multiprocessing import Pool



# set up autentification github
username = 'edigeze'
# token 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
token = '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'

repos_url = 'https://api.github.com/user/repos'

# create a re-usable session object with the user creds in-built
gh_session = requests.Session()
gh_session.auth = (username, token)

# list all pypi package
api = jk_pypiorgapi.PyPiOrgAPI()
list_packages = api.listAllPackages()
n=len(list_packages)
print("Number of packages on pypi.org:", n)

start_time = time.time()

package_info={}
index = 0
linked_package = 0
github_repo_check = 0
for package in list_packages:
    index+=1
    jData = api.getPackageInfoJSON(package[1])

    # size of the doc assuming that the doc size is big meaning that the package is important
    doc_size = len(str(jData))
    try:
        last_update = datetime.strptime("1900-01-01T01:01:01", "%Y-%m-%dT%H:%M:%S")
        amount_of_releases = len(jData["releases"])
        for rkey, rvalue in jData["releases"].items():
            datetime_object = datetime.strptime(rvalue[0]["upload_time"], "%Y-%m-%dT%H:%M:%S")
            if datetime_object > last_update: last_update = datetime_object
    except:
       pass
       #print(f"impossible to fetch releases on {package[1]}")

    try:
        url = None
        if "github" in jData["info"]["home_page"] or "gitlab" in jData["info"]["home_page"]:
            url=jData["info"]["home_page"]
            linked_package += 1
        elif "github" in jData["info"]["download_url"] or "gitlab" in jData["info"]["download_url"]:
            url=jData["info"]["download_url"]
            linked_package += 1
        # elif "https://git"in jData["info"]["description"]:  # looking for git to include github and gitlab
        #     url=re.search("(?P<url>https?://github.com/[^\s]+)", jData["info"]["description"]).group("url")
        #     linked_package += 1
        # elif "https://git"in jData["info"]["description"]:
        #     url=re.search("(?P<url>https?://github.com/[^\s]+)", str(jData)).group("url")
        #     print("la tu deconnes")
        #     linked_package += 1
    except:
         pass
         #print(f"impossible to fetch info of {package[1]}")

    #compute score
    score = 0 if url==None else 20
    delta = datetime.now() - last_update
    score+=max(0,20-delta.days/50)
    score+=min(20, doc_size/1000)
    score+=min(amount_of_releases, 20)

    # connect to stats:
    github_stars=-1 # -1 mean didn't find any repo
    github_last_commit=None

    github_api_timeout = None
    while github_api_timeout is None:
        try:
            if "github" in url and delta.days<700: # we check the repo if it's github and if the last release is less than 2 years old
                url_github = f"https://api.github.com/repos/{url.split('/')[3]}/{url.split('/')[4]}"
                user_data = gh_session.get(url_github).json()
                github_stars=user_data['stargazers_count']
                github_last_commit=user_data['pushed_at']
                github_repo_check += 1
            github_api_timeout = True

        except KeyError:
            if 'message' in user_data:
                github_api_timeout = True
            else:
                print("wait for API github timeout finished")
                time.sleep(60)
        except:
            github_api_timeout = True
            pass

    info = {"url": url,
            "Last_update": last_update,
            "Amount_of_releases": amount_of_releases,
            "Doc_size":doc_size,
            "score": score,
            "github_stars":github_stars,
            "github_last_commit": github_last_commit
            }
    package_info[package[1]] = info

    if index%1000==0:
        print(f'packages parsed : {index} time : {(time.time() - start_time)} repo_check : {github_repo_check}')
        start_time = time.time()

package_info = {k: v for k, v in sorted(package_info.items(), key=lambda item: item[1]["github_stars"])}

for name, info in package_info.items():
    print(name, info)
print(linked_package, len(package_info), github_repo_check)



with open('saved_dictionary.pkl', 'wb') as f:
    pickle.dump(package_info, f)






# with open('saved_dictionary.pkl', 'rb') as f:
#     loaded_dict = pickle.load(f)

# check the important packages without github
# for name, info in package_info.items():
#     if info["Doc_size"]> 10000 and info["url"]==None:
#         print(name)


