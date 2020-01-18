
# Use reinforcement learning to train a flappy bird which NEVER dies  

![always flying](res/307K_flying.gif)

---

## Dependencies

Install **pygame 1.9.6** package first  
Install **python 3.7**

---

## File Structure

- `src/bot.py` - This file contains the `Bot` class that applies the Q-Learning logic to the game.

- `src/flappy.py` - Main program file in python, play the game or train an agent to play the game

- `data/qvalues.json` - Q-table of state-actions in Q-Learning, start a new training by removing this file

- `data/hitmasks_data.pkl` - Mask data to detect crash in non-UI training mode

---

## How to run

``` dos
python3 src/flappy.py [-h] [--fps FPS] [--episode EPISODE] [--ai]
                      [--train {normal,noui,replay}] [--resume]
                      [--max MAX] [--dump_hitmasks]
```

- `-h, --help` : Show usage formation
- `--fps FPS` : number of frames per second, default value:
  - User play or normal training mode with UI: `25`
  - Replay training mode: `20`
  - AI play mode: `60`
- `--episode EPISODE` : Training episode number, default: 10,000
- `--ai` : AI play mode
- `--train {normal,noui,replay}` : Training mode:
  - `normal` : Normal training mode with UI
  - `noui` : Training without UI, fastest training mode
  - `replay` : Training without UI, replay game with UI from last 50 steps once the bird crashes, it provides a visual way to check how bird crashed.
- `--resume` : Resume game from last 50 steps before crash, it's useful to correct flying trajectory for rare scenario. But it's 3x slower than normal mode. When in replay training mode, this flag is enabled automatically.  
- `--max MAX` : Maxium score per episode, restart game if agent reach this score, default: 10,000,000
- `--dump_hitmasks` : dump hitmasks to file and exit

### Play game in user mode

``` dos
python3 src/flappy.py
```

### Train the agent bot without UI, play 1000 times

``` dos
python3 src/flappy.py --train noui --episode 1000
```

### Train the agent bot, replay last 50 steps before crash with UI, restart a new game when the bird reach 1000 scores

``` dos
python3 src/flappy.py --train replay --episode 1000 --max 1000
```

---

## What I've done

After long time training (10+ hours), I ran another test with **Max Score=10M** and **Episode=2**. The game will restart once the bird reaches 10M score. This test demostrates the trained agent can fly for a long time without any crash. Even training without UI, it still need almost 2 hours in my Mac to reach 10M scores. I only run 2 episodes in this test.

<p align="center">
<img src="res/episode_2_max_10M.png" width="500"><br>
<b>Total episode: 2, Max score: 10,000,000</b></p>  

From start point to the first pipe, the bird will fly a long distance without any obstacles, the states before the first pipe won't be same as the following training, the next test demostrates the trained agent deals with the beginning of the journey perfectly. Setting **Max Score=10** and **Episode=20,000**, the agent passed the test without any failure.

<p align="center">
<img src="res/episode_20K_max_10.png" width="500"><br>
<b>Total episode: 20,000, Max score: 10</b></p>  

The 3rd test demostrates the stability and reproducibility for any of the game. In this test, **Max Score=10,000** and **Episode=800**, the trained agent also passed without any failure.  

<p align="center">
<img src="res/episode_800_max_10K.png" width="500"><br>
<b>Total episode: 800, Max score: 10,000</b></p>

I did additional test to see how many score the bird could fly, just for curious. I set **Max Score=50,000,000** for only **One Episode**.  

<p align="center">
<img src="res/50M_Score.png" width="600"></p>

## Conclusion

**The trained agent(flappy bird) NEVER dies.**

---

## Background

To be updated

## How to improve

To be updated

## Steps to train a bird which never dies

1. Set **Max score = 10K**, **Episode = 15K**, enable **resume** mode

``` dos
python3 src/flappy.py --train noui --episode 15000 --max 10000 --resume
```

<p align="center"><img src="res/episode_15K_max_10K.png" width="500"></p>  

2. Set **Max score = 10**, **Episode = 15K**, enable **resume** mode

``` dos
python3 src/flappy.py --train noui --episode 15000 --max 10 --resume
```

<p align="center"><img src="res/episode_15K_max_10.png" width="500"></p>  

3. Repeat step 1 and step 2 alternatively until almost all the episodes end at desired maximum scores.

<p align="center">
<img src="res/episode_1K_max_10K.png" width="400">
<img src="res/episode_100K_max_10.png" width="400">
</p>

4. Set higher **Max score = 10M**, **Episode = 1000**, enable **resume** mode, until it can reach 10M maximum score.

``` dos
python3 src/flappy.py --train noui --episode 1000 --resume
```

<p align="center"><img src="res/episode_2_max_10M_1.png" width="500"></p>  

5. It may take 10+ hours to train a bird to a perfect state from scratch. Validate the AI bot without **resume** flag, it will 3x faster. It costs about 2 hours to reach 10M scores in my Mac. If bird still encounters crash at the beginning phase, try to train more episodes in *step 2*. If bird crashes between pipes, try to train more in *step 1*.

## References

http://sarvagyavaish.github.io/FlappyBirdRL/
https://github.com/chncyhn/flappybird-qlearning-bot  
https://github.com/sourabhv/FlapPyBird
