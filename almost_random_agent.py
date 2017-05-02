import random
import sys
import numpy as np
import random
import tensorflow as tf
import re
import os.path

RADIUS = int(sys.argv[1])

ROWS = 25
COLS = 80
actions = ['level_prev','level_next','move_N','move_NE','move_E','move_SE','move_S','move_SW','move_W','move_NW','rest','open_door','search','kick']
#batchS = 4
n_input =  (RADIUS*2+1)*(RADIUS*2+1)+2# MNIST data input (img shape: 28*28)
n_action = len(actions)
n_hidden_1 = n_input*2 # 1st layer number of features
n_hidden_2 = n_input*2 # 2nd layer number of features
n_rec = n_input


tf.reset_default_graph()

x = tf.placeholder(shape = [None,n_input], dtype = tf.float32)
x_one_hot = tf.one_hot(x,n_hidden_1)
rnn_input = tf.unstack(x_one_hot, axis = 1)
Wr = tf.Variable(tf.random_normal([n_rec, n_hidden_1]))
# W1 = tf.Variable(tf.random_normal([n_rec,n_hidden_1]))
W2 = tf.Variable(tf.random_normal([n_hidden_1,n_hidden_2]))
W3 = tf.Variable(tf.random_normal([n_hidden_2,n_action]))
layer_rec = tf.contrib.rnn.BasicLSTMCell(n_rec)
rnn_output = tf.contrib.rnn.static_rnn(layer_rec, rnn_input, dtype = tf.float32)
layer_1 = tf.matmul(rnn_output, Wr)
layer_1 = tf.nn.relu(layer_1)
layer_2 = tf.matmul(layer_1, W2)
layer_2 = tf.nn.relu(layer_2)
Qout = tf.matmul(layer_2, W3)
predictList = tf.nn.softmax(Qout)
predict = tf.argmax(predicty,1)

nextQ = tf.placeholder(shape=[None,len(actions)], dtype = tf.float32)
# loss = tf.reduce_sum(tf.square(nextQ - Qout))
loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=pred, labels=nextQ))
trainer = tf.train.GradientDescentOptimizer(learning_rate=0.1)
updateModel = trainer.minimize(loss)

init = tf.initialize_all_variables()

rewardFile = open('rewards.txt', 'w')
rewardFile.write("start")
rewardFile.close()
posFile = open('pos.txt', 'w')
posFile.close()
rewardStep = open("individual_reward.txt", 'w')
rewardStep.close()


z = 0.99
e = 0.1
num_episodes = 50000
max_trials = 900000

jList = []
rList = []

saver = tf.train.Saver()

with tf.Session() as sess:
    sess.run(init)
    if os.path.isfile("model_422.ckpt"):
        rewardFile = open('rewards.txt', 'a')
        rewardFile.write("restore")
        rewardFile.close()
        saver.restore(sess, "model_422.ckpt")

    for i in range(num_episodes):
        rAll = 0
        d = False
        j = 0

	#print "Dont delete this"

        raw = raw_input()
        if raw == 'end':
            #end signals we died or whatever
            #print "exiting"
	    break
        else:
            #game is still going
            level = int(raw_input())
            hp = int(raw_input())

            #read map
            gameMapS = ""
            for row in range(ROWS):
                gameMapS += raw_input()
            gameMap = list(gameMapS)
	    
            # for isdf in range(len(gameMap)):
            #     gameMap[isdf] = ord(gameMap[isdf])


            x = raw_input()
            y = raw_input()
	    posFile = open('pos.txt', 'a')
	    posFile.write("x:" + str(x) + " y:" + str(y))
	    posFile.close()

            #read neighborhood
            nbS = ""
            nb = list()
            for i in range(0,RADIUS*2+1):
                nbS += raw_input()
            nb = list(nbS)
            # for i in range(len(nb)):
            #     nb[i] = ord(nb[i])
            nb.append(x)
            nb.append(y)
    	while j < 900000:
            j += 1
            #r = reward
            #d = death
	    # gameMap = tf.reshape(gameMap, [1,2000]).eval()
        #     a,allQ = sess.run([predict,Qout], feed_dict={input:gameMap})
            nb = tf.reshape(nb, [None,n_input]).eval()
            a,allQ = sess.run([predict,Qout], feed_dict={x:nb})
            if np.random.rand(1) < e:
                a[0] = random.randint(0,13)
            print actions[a[0]]

            #s1,r,d,_
            raw1 = raw_input()
     	    if raw1 == 'end':
     	        #end signals we died or whatever
                d = True
                gameMap1 = gameMap
            else:
                #game is still going
                level = int(raw_input())
                hp = int(raw_input())
             	#read map
                gameMapS1 = ""
    	        gameMap1 = list()
                for i in range(0,ROWS):
             	     line = raw_input()
             	     gameMapS1 += line
                gameMap1 = list(gameMapS1)
		explored = 0
	    	    for c in gameMap1:
			if c != ' ':
		    	     explored+=1
                # for isdf in range(len(gameMap1)):
                #     gameMap1[isdf] = ord(gameMap1[isdf])

                x1 = raw_input()
                y1 = raw_input()
		posFile = open('pos.txt', 'a')
	    	posFile.write("x:" + str(x1) + " y:" + str(y1))
	   	posFile.close()

         	#read neighborhood
         	nbS1 = ""
            nb1 = list()
            for i in range(0,RADIUS*2+1):
                nbS1 += raw_input()
            nb1 = list(nbS1)
            # for i in range(len(nb1)):
            #     nb1[i] = ord(nb1[i])
            nb1.append(x1)
            nb1.append(y1)

            #reward here
            # index = 80*20
            # reward = 0
            # HP = False
            # while (not HP) or index <= 80*21:
            #     if gameMap1[index] == ord('H') and gameMap1[index+1] == ord('P'):
            #         HP = True
            #     if HP:
            #        index+=3
            #        while gameMap1[index] != ord('('):
            #            reward = reward*10 + gameMap1[index] - ord('0')
            #            index += 1
            #     else:
            #        reward = -1000

            reward = hp + (level - 1)*10000 + explored
            if d == True:
                reward -= 1000
	    nb1 = tf.reshape(nb1, [None,n_input]).eval()
            Q1 = sess.run(Qout,feed_dict={x:nb1})
            maxQ1 = np.max(Q1)
            targetQ = allQ
            targetQ[0,a[0]] = reward + z*maxQ1
            _,loss1 = sess.run([updateModel, loss], feed_dict={x:nb, nextQ:targetQ})
            rAll += reward
	    rewardStep = open("individual_reward.txt", 'a')
	    rewardStep.write("Reward: " + str(reward))
	    rewardStep.close()
            nb = nb1
            if d == True:
     	        #end signals we died or whatever
     	        e = 1./((i/50) + 10)
                #print "exiting"
		break
	saver.save(sess, "model_422.ckpt")
	rewardFile = open("rewards.txt", 'a')
	rewardFile.write("Reward for attempt " + str(i) + " is " + str(rAll))
	rewardFile.close()
        jList.append(j)
        rList.append(rAll)
