/* vxi11cc_python.i */
 %module vxi11cc
 %{

# local version to avoid complexity for swig

typedef struct {
	void  *client;
	void  *link;
} CLINK;

# include "vxi11cc_python.h";

 %}

# local version to avoid complexity for swig

typedef struct {
	void  *client;
	void  *link;
} CLINK;

# include "vxi11cc_python.h";

