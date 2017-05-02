This git repository holds all modified or new files related to a Reinforcement Learning algorithm for the game NetHack.

New Files:



Modified Files:
src/mkobj.c: in 4 probability arrays at the top, set all probabilities to 0 except for food, which was set to 100
src/makemon.c: around line 960, as a check before is_golem() (making that an else if), if it's a floating eye, give it 1000 HP
src/monst.c: redefine MON macro to add 6 to each level, add new macro ROCMON that is the old MON, change desired monsters to have level 0 and use ROCMON. Can change other monster stats, though behavior is difficult to predict.



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



