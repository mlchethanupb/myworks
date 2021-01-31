/*Data structures for communication through the AODV protocol.*/ 

#ifndef _AODV_H_
#define _AODV_H_

#include "net/rime/rime.h"
#include "lib/list.h"
#include "lib/memb.h"

struct route_request {
	
	linkaddr_t src_addr;
	int src_seq_num;
	int broadcast_id;
	linkaddr_t dest_addr;
	int dest_seq_num;
	int hop_cnt;
};


struct route_reply {
	
	linkaddr_t src_addr;
	linkaddr_t dest_addr;
	int dest_seq_num;
	int hop_cnt;
	int lifetime;
};

struct route_error{
	
	linkaddr_t src_addr;
	linkaddr_t dest_addr;
	int dest_seq_num;
};

struct route_table_entry{
	struct route_table_entry *next;
	int valid;
	linkaddr_t dest_addr;
	linkaddr_t nxt_hop;
	int seq_num;
	int hop_cnt;
	int lifetime;//Check for the data type	
};

struct packet_data{
	linkaddr_t src_addr;
	linkaddr_t dest_addr;
	int dest_seq_num;
	char data[10];
};





#endif /*_AODV_H_*/
