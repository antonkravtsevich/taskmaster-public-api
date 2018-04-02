#!/bin/sh
echo Build docker container

docker login -u $DOCKER_USER -p $DOCKER_PASS

echo Docker username: $(docker info | sed '/Username:/!d;s/.* //')

if [ "$TRAVIS_BRANCH" = "master" ]; then
    TAG="latest"
else
    TAG="$TRAVIS_BRANCH"
fi

echo Build docker container
docker build -f Dockerfile -t $TRAVIS_REPO_SLUG:$TAG .

echo Result:
echo $(docker images | grep taskmaster)

docker push $TRAVIS_REPO_SLUG