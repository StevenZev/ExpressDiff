# ExpressDiff
Differential Analysis Pipeline for RNA-Seq Data

# Setup
## Go to ood.hpc.virginia.edu to start a Desktop interactive job and a JupyterLab job
if prompted, sign in with UVA account
### Find the button to start interactive jobs in the taskbar on top
![image_info](pictures/ood_dashboard.png)
### Choose Desktop or JupyterLab from the dropdown
![image_info](pictures/dropdown.png)
For the JupyterLab job, we recommend allocating around 64GB of memory (but if your files are larger, you may need to add more!)
![image_info](pictures/jupyter.png)
You can also create a new job by selecting from the menu on the left
After creating a job, you should be brought to a page that shows your interactive jobs (this is what it looks like after creating both jobs):
![image_info](pictures/interactive_jobs.png)
if they say Queued or Starting, you may need to wait for a moment.
### Click the "Connect to Jupyter" and "Launch Desktop" buttons to open the interactive jobs
the JupyterLab tab will open a terminal for you, but it may not be in the right directory. Use this command to see the directory you are in.
```shell
pwd
```
For example, I have an empty directory called Example (can see on sidebar on the left), but the initial terminal is not in that same directory:
![image_info](pictures/wrong_directory.png)
if it's in the wrong directory, can click the + icon to open the launcher, then scroll down and open a new terminal to quickly go to the directory you have open in the sidebar
![image_info](pictures/launcher.png)
## Clone Git Repository
run this command in the terminal after checking that you are in the right directory
```shell
git clone https://github.com/StevenZev/ExpressDiff.git
```
then run this command to go into the repository you just cloned
```shell
cd ExpressDiff
```
would look something similar to this:
![image_info](pictures/clone.png)
I used this command to check the contents of the current directory:
```shell
ls
```
Then, can click on the ExpressDiff folder on the left to open it in the sidebar
## Open setup.ipynb (from the sidebar on the left)
### Hit button to restart kernel and run all cells
### Make sure to use Python3 kernel
![image info](pictures/run.png)
## Scroll to bottom and copy the Network URL
![image info](pictures/networkurl.png)
## Go to the Desktop interactive job tab and open a web browser (Firefox is already installed) then paste in the Network URL in a new tab to open app
![image_info](pictures/desktop.png)

# MEMORY
if you see this, then you may need to allocate more memory:
![image_info](pictures/error.png)