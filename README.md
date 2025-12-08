```
docker pull ghcr.io/backwaterroyal/micromouse:main
docker run -p 6969:6969 ghcr.io/backwaterroyal/micromouse:main
```

This package implements Micromouse through use of a set of API endpoints. This attempts to simulate the game as accurately as possible, with the only information gleaned directly from the API being the obstruction status of the 4 directions surrounding your "mouse." Hitting the endpoint /mouse/<MOUSE_NAME>/surroundings returns json like {forward: true, backwards: false, left: true, right: true}, with these booleans representing whether there is a wall in the related direction.

The movement endpoint /mouse/<MOUSE_NAME>/move accepts a POST of a direction to move in, and returns status based on whether it worked. The return from this endpoint also includes things like whether you have reached the goal state, and returns a flag if the end state has been reached.

The technical details of the API are contained in a Swagger page that is started alongside the container, found at <URL>/docs

[!NOTE]
I havent done this yet, but i may remove the swagger doc when the server is started in CTF mode (with --ctf). To make it a little more challenging for players and force them to explore the endpoints on their own. Maybe provide a helptext

The simplest possible algorithm that can solve mazes with 100% accuracy is called "Wall Follower," an example of which is found in the scripts directory of this repository. "min_wallfollower.py"

Some other examples of algorithms that could be implemented to solve the mazes are here

https://en.wikipedia.org/wiki/Maze-solving_algorithm

Actually pretty interesting reading, would recommend.
