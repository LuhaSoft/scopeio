 /* vxi11_python.i */
 %module vxi11
 %{
 /* Put header files here or function declarations like below */

int        open(char *device_ip, char *device_name);
int        cmd(char *cmd);
long long  resp(int index);
int        close(char *device_ip);

 %}


int        open(char *device_ip, char *device_name);
int        cmd(char *cmd);
long long  resp(int index);
int        close(char *device_ip);
 
