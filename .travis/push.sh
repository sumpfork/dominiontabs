#!/bin/sh

setup_git() {
    git config --global user.email "travis@travis-ci.org"
    git config --global user.name "Travis CI"
    git config --global push.default current
}

commit_carddb_files() {
    git status
    git stash
    git checkout $TRAVIS_BRANCH
    git stash pop
    git add src/domdiv/card_db
    git commit --message "Travis build: $TRAVIS_BUILD_NUMBER"
}

upload_files() {
    git remote remove origin
    git remote add origin https://${GH_TOKEN}@github.com/${TRAVIS_REPO_SLUG}.git >/dev/null 2>&1
    echo "pushing to origin $TRAVIS_BRANCH"
    git push origin $TRAVIS_BRANCH
}

echo "Branch: $TRAVIS_BRANCH"
setup_git
commit_carddb_files
upload_files

# credit: https://gist.github.com/willprice/e07efd73fb7f13f917ea
