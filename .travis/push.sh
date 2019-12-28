#!/bin/sh

setup_git() {
    git config --global user.email "travis@travis-ci.org"
    git config --global user.name "Travis CI"
}

commit_carddb_files() {
    git diff
    git add src/domdiv/card_db
    git commit --message "Travis build: $TRAVIS_BUILD_NUMBER"
}

upload_files() {
    git remote remove origin
    git remote add origin https://${GH_TOKEN}@github.com/sumpfork/dominiontabs.git >/dev/null 2>&1
    echo "pushing to origin $TRAVIS_BRANCH"
    git push origin $TRAVIS_BRANCH
}

echo "Branch: $TRAVIS_BRANCH"
setup_git
commit_carddb_files
upload_files

# credit: https://gist.github.com/willprice/e07efd73fb7f13f917ea
