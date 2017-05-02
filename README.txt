This git repository holds all modified or new files related to a Reinforcement Learning algorithm for the game NetHack.

New Files:
nethack2.py
agent423.py: deep recurrent reinforcement learning agent
almost_random_agent.py: single-layer feed-forward neural network with q-learning implementation



Modified Files:
src/mkobj.c: in 4 probability arrays at the top, set all probabilities to 0 except for food, which was set to 100
src/makemon.c: around line 960, as a check before is_golem() (making that an else if), if it's a floating eye, give it 1000 HP
src/monst.c: redefine MON macro to add 6 to each level, add new macro ROCMON that is the old MON, change desired monsters to have level 0 and use ROCMON. Can change other monster stats, though behavior is difficult to predict.
nethack2.py: modified version of shrieker git repositiory. Runs agent and executable as subprocesses and polls agent for next move when decision needs to be made that is not handled natively by the server
random_agent.py: agent which randomly picks its move from the shortlist of predefined moves


How to compile the game:
    (to create initial Makefiles after you've downloaded the NetHack source from https://github.com/NetHack/NetHack):
      in sys/(your_system):
        ./setup.sh

    (to change where the executable goes)
      in top directory
        change the variable HACKDIR (possibly by modifying PREFIX) to the desired location

    (to compile the game)
      in top directory
        make install



How to play the game:
    (in the directory you specified in top level Makefile before compiling)
      ./nethack



How to run the python script to train the neural network:
    python nethack2.py number_of_episodes



