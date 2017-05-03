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
actions = ['level_prev','level_next','move_N','move_NE','move_E','move_SW','move_S','move_SE','move_W','move_NW','rest','open_door','search','kick']
#batchS = 4
n_input =  (RADIUS*2+1)*(RADIUS*2+1)# MNIST data input (img shape: 28*28)
n_action = len(actions)
n_item = 18
n_hidden_1 = n_input*2 # 1st layer number of features
n_hidden_2 = n_input*2 # 2nd layer number of features
n_rec = n_input

tf.reset_default_graph()

x = tf.placeholder(shape = [None,n_input], dtype = tf.int32)
x_one_hot = tf.one_hot(x, n_item)
rnn_input = tf.unstack(x_one_hot, axis = 1)
Wr = tf.Variable(tf.random_normal([n_rec, n_hidden_1]))
# W1 = tf.Variable(tf.random_normal([n_rec,n_hidden_1]))
W2 = tf.Variable(tf.random_normal([n_hidden_1,n_hidden_2]))
W3 = tf.Variable(tf.random_normal([n_hidden_2,n_action]))
layer_rec = tf.contrib.rnn.BasicLSTMCell(n_rec)
rnn_output,final_state = tf.contrib.rnn.static_rnn(layer_rec, rnn_input, dtype = tf.float32)
layer_1 = tf.matmul(rnn_output[-1], Wr)
layer_1 = tf.nn.relu(layer_1)
layer_2 = tf.matmul(layer_1, W2)
layer_2 = tf.nn.relu(layer_2)
Qout = tf.matmul(layer_2, W3)
predictList = tf.nn.softmax(Qout)
predict = tf.argmax(predictList,1)

nextQ = tf.placeholder(shape=[None,len(actions)], dtype = tf.float32)
loss = tf.reduce_sum(tf.square(nextQ - Qout))
# loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=Qout, labels=nextQ))
trainer = tf.train.AdamOptimizer(learning_rate=0.1)
updateModel = trainer.minimize(loss)


init = tf.global_variables_initializer()

saver = tf.train.Saver()

# rewardFile = open('rewards.txt', 'w')
# rewardFile.write("start")
# rewardFile.close()
posFile = open('pos.txt', 'w')
posFile.close()
rewardStep = open("individual_reward.txt", 'w')
rewardStep.close()

d = True


def readInput():
    global d
    raw = raw_input()
    if raw == 'end':
        d = True
        nbIndecies = list()
        for i in range((RADIUS*2+1)*(RADIUS*2+1)):
            nbIndecies.append(0)
        explored = 0
    else:
        #game is still going
        d = False
        explored = 0
        level = int(raw_input())
        hp = int(raw_input())
        #read map
        gameMapS = ""
        for row in range(ROWS):
            gameMapS += raw_input()
        gameMap = list(gameMapS)
        for isdf in range(len(gameMap)):
            # posFile = open('pos.txt', 'a')
            # posFile.write(gameMap[isdf])
            # posFile.close()
            if gameMap[isdf] != ' ':
                explored += 1
        #current position
        x = raw_input()
        y = raw_input()
        posFile = open('pos.txt', 'a')
        posFile.write("x:" + str(x) + " y:" + str(y) + "\n")
        posFile.close()
        #read neighborhood
        nbS = ""
        nb = list()
        for i in range(0,RADIUS*2+1):
            nbS += raw_input()
        nb = list(nbS)
        # for isdf in range(len(nb)):
        #     posFile = open('pos.txt', 'a')
        #     posFile.write(nb[isdf])
        #     posFile.close()
        nbIndecies = list()
        for i in range(len(nb)):
            # rewardFile = open('rewards.txt', 'a')
            # rewardFile.write(nb[i])
            # rewardFile.close()
            if nb[i] == '-':
                nbIndecies.append(0)
            elif nb[i] == '|':
                nbIndecies.append(1)
            elif nb[i] == '.':
                nbIndecies.append(2)
            elif nb[i] == '#':
                nbIndecies.append(3)
            elif nb[i] == '>':
                nbIndecies.append(4)
            elif nb[i] == '<':
                nbIndecies.append(5)
            elif nb[i] == '+':
                nbIndecies.append(6)
            elif nb[i] == '@':
                nbIndecies.append(7)
            elif nb[i] == '$':
                nbIndecies.append(8)
            elif nb[i] == '^':
                nbIndecies.append(9)
            elif nb[i] == ')':
                nbIndecies.append(10)
            elif nb[i] == '[':
                nbIndecies.append(11)
            elif nb[i] == '%':
                nbIndecies.append(12)
            elif nb[i] == '{':
                nbIndecies.append(13)
            elif nb[i] == 'e':
                nbIndecies.append(14)
            elif nb[i] == 'x':
                nbIndecies.append(15)
            elif nb[i] == ' ':
                nbIndecies.append(16)
            else:
                nbIndecies.append(17)

    return nbIndecies,explored


z = 0.99
e = 0.1
max_trials = 900000


with tf.Session() as sess:
    # sess.run(init)
    # if os.path.isfile("model_423.ckpt"):
    # rewardFile = open('rewards.txt', 'a')
    # rewardFile.write("\nNew Session\n")
    # rewardFile.close()
    # saver.restore(sess, "/tmp/model.ckpt")
    new_saver = tf.train.import_meta_graph("model.ckpt.meta")
    new_saver.restore(sess, tf.train.latest_checkpoint('./'))

    hp = 0
    level = 0
    rAll = 0
    d = False
    j = 0

    # print "Dont delete this"

    nb,explored = readInput()

    while j < max_trials:
        j += 1
        #r = reward
        #d = death
        # gameMap = tf.reshape(gameMap, [1,2000]).eval()
        #     a,allQ = sess.run([predict,Qout], feed_dict={input:gameMap})
        nb = np.reshape(nb, (1,n_input))
        a,allQ = sess.run([predict,Qout], feed_dict={x:nb})
        if np.random.rand(1) < e:
            a[0] = random.randint(0,13)
        print actions[a[0]]

        #s1,r,d,_
        nb1,explored1 = readInput()

        reward = hp + level*10000 + explored

        if d == True:
            reward -= 1000
            nb1 = nb
            explored1 = explored

        nb1 = np.reshape(nb1, (1,n_input))

        Q1 = sess.run(Qout,feed_dict={x:nb1})

        maxQ1 = np.max(Q1)
        targetQ = allQ
        targetQ[0,a[0]] = reward + z*maxQ1

        _,loss1 = sess.run([updateModel, loss], feed_dict={x:nb, nextQ:targetQ})
        rAll += reward
        rewardStep = open("individual_reward.txt", 'a')
        rewardStep.write("Reward: " + str(reward) + "\n")
        rewardStep.close()
        nb = nb1
        explored = explored1

        if d == True:
            #end signals we died or whatever
            #print "exiting"
            saver.save(sess, "model.ckpt")
            rewardFile = open("rewards.txt", 'a')
            rewardFile.write(str(rAll) + " " + str(reward) + "\n")
            rewardFile.close()
            jFile = open("step.txt", 'a')
            jFile.write(str(j) + "\n")
            jFile.close()
            # print "exiting"
            break
