typedef struct {
	CLINK  *clink;
	char   *buffer;
	long   buffer_size;
	char   *device_ip;
	char   *device_name;
} PLINK;

PLINK      *iconnect(char *device_ip, long buffer_size, char *device_name);
int         icommand(PLINK *plink,char *cmd, long timeout_ms);
long long   iresponse(PLINK *plink, int index);
int         idisconnect(PLINK *plink);

