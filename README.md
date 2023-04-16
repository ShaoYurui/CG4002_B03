# CG4002_B03

## Hardware AI

The CNN.ipynb file in the Software_AI folder runs the software implementation for 1D CNN for action classification.

In the hls subfolder, the cnn.cpp file runs the implementation of the 1D CNN 2 player game. The cnn_test.cpp is used to run the test cases on the implementation.

In the ultra96 subfolder, the bitstream and hardware handoff files to be overlaid using pynq is cnnlast12.bit and cnnlast12.hwh. The file ultra96_cnn.py provides helper functions to overlay the bit file and run inference. To test the AI system, run the function set_up_fpga before running the function test_FPGA. To test the AI, the python script must be executed from root using the command:

```sh
 sudo -E python ultra96_cnn.py
```

## Internal Comms

On a linux based laptop or other similar system, the “Internal Comms/main.py” is the only file needed to run the relay node. It uses a library bluepy, which must be installed beforehand using:
```sh
pip install bluepy
```
Inside main.py contains a variable PLAYER_ID which determines whether the node will be used for player 1 or 2. This must be edited accordingly before running the file.

The port number used in each file is declared in “port” variable which must also be edited according to the port number used in the next step.

Before running the file, local port forwarding must be performed on another terminal to establish a tunnel to the ultra96. This can be done by running:
```sh
ssh -L 8049:192.168.95.249:8049 <your_stu_server>
```
then running:
```sh
ssh xilinx@192.168.95.249
```
On another relay node, the similar steps must also be done, but with a different port number by running:
```sh
ssh -L 8050:192.168.95.249:8050 <your_stu_server>
```
followed by
```sh
ssh xilinx@192.168.95.249
```
After the tunnel is established on each relay node and the eval_client already connected to the eval_server on the External Comms side, the file can be executed by running: 
```sh
python main.py 
```
The node will then begin connecting to the hardware devices. A device is successfully connected to the relay node when a text “Device[n] connected” is shown, where n is a number from 0 (gun), 1 (vest), and 2 (glove). Once all three devices are connected to the relay node, that player is considered ready for the game. In a two player game, all three devices should be connected to both relay nodes before the game can start.

## External Comms

Once the SSH tunnels have been created during the Internal Comms setup process, we have to set up 2 terminal sessions. One for the evaluation server and the other for running the External Comms code. Both terminal windows will first ssh into the SSH jump server using the command: 
```sh
ssh <my_jump_server>
```
for the window running the main code
```sh
ssh -X <my_jump_server>
```
for the window running the evaluation server code. 

Then both windows will ssh into the Ultra96 using the command: 
```sh
ssh xilinx@192.168.95.249
```
for the window running the main code
```sh
ssh -X xilinx@192.168.95.249
```
for the window running the evaluation server code. 

Once both windows have reached the Ultra96, run the following command to go into the right directory: 
```sh
cd CG4002/External\ Comms/
```
Then activate the virtual environment with the command
```sh
source capstone/bin/activate
```

Now we can start up the evaluation server using the command
```sh
python3 eval_server.py 8080 B03 <number>
```
Where <number> is 1 if you want to play a 1-person game, and 2 for multi-person game. Wait for the eval_server GUI to show up. 

Now run the main Ultra96 code with the command
```sh
sudo -E python3 main_ultra96.py <number>
```
Where <number> is 0 for 1-person game and 1 for multi-person game. 

Now the eval_server window should be prompting for a secret key, which is 1212121212121212. Key it in and the eval_server is now connected. 

Wait for the relay nodes to indicate that all devices are connected, then the game can start.
