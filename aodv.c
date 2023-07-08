#include "contiki.h"
#include "net/rime/rime.h"
#include "random.h"
#include "dev/button-sensor.h"
#include "dev/leds.h"
#include <stdio.h>
#include <string.h>
#include "aodv.h"


/*---------------------------------------------------------------------------*/

/*Process declarations*/

PROCESS(aodv_process, "AODV Process");
AUTOSTART_PROCESSES(&aodv_process);


/*MACRO*/
#define MAX_TABLE_COUNT 10
#define TRUE 1
#define FALSE 0

LIST(route_table);
MEMB(route_mem, struct route_table_entry, MAX_TABLE_COUNT);


/*Global Variables Declarations*/

static struct broadcast_conn broadcast;
static struct unicast_conn uc;
static int seq_num_cntr = 0 ;
static struct route_request rcvd_req_data;
static struct route_reply rcvd_rep_data;
static struct route_error rcvd_err;
static struct packet_data rcvd_data; 

/*Function prototype declarations*/

static void broadcast_recv(struct broadcast_conn *c, const linkaddr_t *from); // Callback for broadcast. 
static void unicast_recv(struct unicast_conn *c, const linkaddr_t *from); // Callback for unicast. 

/* Routing table function declarations */
void route_table_init(void);
struct route_table_entry * route_table_add( const int valid, const linkaddr_t* dest_addr, const linkaddr_t * nexthop, const int seq_num ,const int hop_cnt,const int lifetime );
struct route_table_entry * route_table_find(const linkaddr_t *dest);
void route_table_remove(struct route_table_entry *e);
void route_table_delete_all(void);


static const struct broadcast_callbacks broadcast_cb = {broadcast_recv};
static const struct unicast_callbacks unicast_cb = {unicast_recv};

/*============================================================================*/
			/*Broadcast Code*/
/*============================================================================*/

/*---------------------------------------------------------------------------*/
/* 
 * Define callbacks function
 * Called when a packet has been received by the broadcast module
 */
static void broadcast_recv(struct broadcast_conn *c, const linkaddr_t *from) {
    /* 
     * Function: void* packetbuf_dataptr()
     * Get a pointer to the data in the packetbuf
     * Using appropriate casting operator for data
     */
    printf("Broadcast message received from %d.%d with length %d\n", from->u8[0], from->u8[1],  packetbuf_datalen());

	//printf("sizeof(rcvd_req_data) : %d , sizeof(rcvd_rep_data) : %d, sizeof(rcvd_err) : %d \n  ", sizeof(rcvd_req_data), sizeof(rcvd_rep_data), sizeof(rcvd_err));

	memcpy(&rcvd_req_data,(struct route_request *)packetbuf_dataptr(), sizeof(rcvd_req_data));

	printf("broadcast_recv -- Message Received : \n\n src_addr - %d.%d \n src_seq_num : %d , broadcast_id : %d \n dest_addr : %d.%d \n dest_seq_num : %d , hop_cnt : %d \n",\
				 rcvd_req_data.src_addr.u8[0], rcvd_req_data.src_addr.u8[1], rcvd_req_data.src_seq_num, rcvd_req_data.broadcast_id, \
				 rcvd_req_data.dest_addr.u8[0], rcvd_req_data.dest_addr.u8[1], rcvd_req_data.dest_seq_num , rcvd_req_data.hop_cnt );

	/*Check if the just broadcasted messages is received back. */

	struct route_table_entry * src_entry = route_table_find(&(rcvd_req_data.src_addr));
	struct route_table_entry * dest_entry = route_table_find(&(rcvd_req_data.dest_addr));
	
	//if(src_entry!=NULL){ printf("soruce seq num stored : %d \n",src_entry->seq_num ); } else {printf("no src_entry");}

	if((src_entry == NULL) || (rcvd_req_data.src_seq_num > src_entry->seq_num ))
	{

		/*Add the source of the message sender to the Route Table*/
		if(!linkaddr_cmp(&(rcvd_req_data.src_addr), &linkaddr_node_addr))
		route_table_add(TRUE, &(rcvd_req_data.src_addr),from ,rcvd_req_data.src_seq_num, rcvd_req_data.hop_cnt+1, 0);//currently lifetime is considered 0
		
		/*
		 * 	Check if this is the destination node.
		 	Yes: send the RREP packet. 
		  	No :
				 Do you have destination address with fresh sequence num ?  
				 yes :  send the RREP to source. 					
			No information at all --- Broadcast the message to neighbours. 
		 */
		if(linkaddr_cmp(&(rcvd_req_data.dest_addr), &linkaddr_node_addr))
		{

			/* Frame the response packet */

			struct route_reply reply;
			
			linkaddr_copy(&(reply.src_addr),&linkaddr_node_addr);
			linkaddr_copy(&(reply.dest_addr),&(rcvd_req_data.src_addr));  
			reply.dest_seq_num = 1;
			reply.hop_cnt = 0;
			reply.lifetime = 0;

			packetbuf_copyfrom(&reply, sizeof(reply));
			
			/* linkaddr_node_addr: RIME address of the current node */
			/* Sender's address must be different from destination address */
			if (!linkaddr_cmp(from, &linkaddr_node_addr))
			{
			    unicast_send(&uc, from);
			}
		}
		else if((dest_entry != NULL) && (dest_entry->valid == TRUE) && (rcvd_req_data.dest_seq_num < dest_entry->seq_num)) 
		{

			/* Frame the response packet */

			struct route_reply reply;
			
			linkaddr_copy(&(reply.src_addr),&(dest_entry->dest_addr));
			linkaddr_copy(&(reply.dest_addr),&(rcvd_req_data.src_addr));  
			reply.dest_seq_num = dest_entry->seq_num;
			reply.hop_cnt = dest_entry->hop_cnt + 1;
			reply.lifetime = dest_entry->lifetime;

			packetbuf_copyfrom(&reply, sizeof(reply));
			
			/* linkaddr_node_addr: RIME address of the current node */
			/* Sender's address must be different from destination address */
			if (!linkaddr_cmp(from, &linkaddr_node_addr))
			{
			    unicast_send(&uc, from);
			}
		}
		else
		{
			/*Increase the hop count and forward the data*/
			rcvd_req_data.hop_cnt = rcvd_req_data.hop_cnt + 1;

			packetbuf_copyfrom(&rcvd_req_data, sizeof(rcvd_req_data));
			
			/* Send broadcast packet */
			broadcast_send(&broadcast);
			
			printf("Forwarding the packect with broadcast id : %d \n",rcvd_req_data.broadcast_id );
		}
	}
	else if((rcvd_req_data.src_seq_num == src_entry->seq_num ))
	{
		if(rcvd_req_data.hop_cnt < src_entry->hop_cnt )
		{
			printf("Updating route table for destination : %d.%d, previous hc : %d , new hc : %d \n ",
				 rcvd_req_data.src_addr.u8[0], rcvd_req_data.src_addr.u8[1], src_entry->hop_cnt, rcvd_req_data.hop_cnt );

			if(!linkaddr_cmp(&(rcvd_req_data.src_addr), &linkaddr_node_addr))
			route_table_add(TRUE, &(rcvd_req_data.src_addr),from ,rcvd_req_data.src_seq_num, rcvd_req_data.hop_cnt+1, 0);//currently lifetime is considered 0
		}

	}

	memset(&rcvd_req_data,0x00,sizeof(rcvd_req_data));

}

/*============================================================================*/
			/*Unicast Code*/
/*============================================================================*/

/*---------------------------------------------------------------------------*/
/* 
 * Define callbacks function
 * Called when a packet has been received by the unicast module
 */
static void unicast_recv(struct unicast_conn *c, const linkaddr_t *from) {

	printf("unicast message received from %d.%d with length : %d\n", from->u8[0], from->u8[1],  packetbuf_datalen());

	/*	RREP message	 */
	if(packetbuf_datalen() == sizeof(rcvd_rep_data) )
	{	

		memcpy(&rcvd_rep_data,(struct route_reply *)packetbuf_dataptr(), sizeof(rcvd_rep_data));

		printf("unicast_recv -- Reply Message Received : \n src_addr - %d.%d \n dest_addr : %d.%d  \n dest_seq_num : %d , hop_cnt : %d \n lifetime : %d \n",\
					 rcvd_rep_data.src_addr.u8[0], rcvd_rep_data.src_addr.u8[1], rcvd_rep_data.dest_addr.u8[0], rcvd_rep_data.dest_addr.u8[1], \
					 rcvd_rep_data.dest_seq_num, rcvd_rep_data.hop_cnt, rcvd_rep_data.lifetime );

		/*Add the source of the message sender to the Route Table*/
		if(!linkaddr_cmp(&(rcvd_rep_data.src_addr), &linkaddr_node_addr))
		route_table_add(TRUE, &(rcvd_rep_data.src_addr),from ,rcvd_rep_data.dest_seq_num, rcvd_rep_data.hop_cnt+1, rcvd_rep_data.lifetime);//currently lifetime is considered 0

		/*Node is the source*/
		if(linkaddr_cmp(&(rcvd_rep_data.dest_addr), &linkaddr_node_addr)) 
		{
			printf("Path to the source and sink has been established, Sending Data\n");

				
				struct packet_data data_sent;
				linkaddr_copy(&(data_sent.src_addr),&linkaddr_node_addr);
				linkaddr_copy(&(data_sent.dest_addr),&rcvd_rep_data.src_addr);
				data_sent.dest_seq_num =rcvd_rep_data.hop_cnt;
				strcpy(data_sent.data, "Chethan");

				 /* Copy data to the packet buffer*/
				packetbuf_copyfrom(&data_sent, sizeof(data_sent));
					
				/* linkaddr_node_addr: RIME address of the current node */
				/* Sender's address must be different from destination address */
				if (!linkaddr_cmp(from, &linkaddr_node_addr)) {
				    unicast_send(&uc, from);
				}
		}
		else/*Not source, forward the data to source */
		{
			struct route_table_entry * entry = route_table_find(&(rcvd_rep_data.dest_addr));

			printf("Next hop address is : %d.%d \n", entry->nxt_hop.u8[0] ,entry->nxt_hop.u8[1] );
			rcvd_rep_data.hop_cnt = rcvd_rep_data.hop_cnt + 1 ;
			 /* Copy data to the packet buffer*/
			packetbuf_copyfrom(&rcvd_rep_data, sizeof(rcvd_rep_data));
			
			/* linkaddr_node_addr: RIME address of the current node */
			/* Sender's address must be different from destination address */
			if (!linkaddr_cmp(&(entry->nxt_hop), &linkaddr_node_addr)) {
			    unicast_send(&uc, &(entry->nxt_hop));
			}
		}
	}
	/*	RERR message 	*/
	else if(packetbuf_datalen() == sizeof(rcvd_err))
	{
		memcpy(&rcvd_err,(struct route_error *)packetbuf_dataptr(), sizeof(rcvd_err));

		printf("unicast_recv -- Error Message Received : src_addr - %d.%d \n  dest_addr : %d.%d  \n dest_seq_num : %d \n",\
					 rcvd_err.src_addr.u8[0], rcvd_err.src_addr.u8[1],rcvd_err.dest_addr.u8[0], rcvd_err.dest_addr.u8[1], rcvd_err.dest_seq_num );

		if(!linkaddr_cmp(&(rcvd_err.src_addr), &linkaddr_node_addr))
		{/* Enter Only if current node is not the source address for whom the error message was intended too*/

			struct route_table_entry * entry = route_table_find(&(rcvd_err.dest_addr));
			
			if(entry != NULL)
			{
				entry->valid = FALSE;
				if((entry->seq_num) < (rcvd_err.dest_seq_num))
				{
					entry->seq_num = rcvd_err.dest_seq_num  ;
				}

				struct route_table_entry * entry = route_table_find(&(rcvd_err.src_addr));

				if(entry != NULL){

					printf("Next hop address is : %d.%d \n", entry->nxt_hop.u8[0] ,entry->nxt_hop.u8[1] );
					 /* Copy data to the packet buffer*/
					packetbuf_copyfrom(&rcvd_err, sizeof(rcvd_err));
					
					/* linkaddr_node_addr: RIME address of the current node */
					/* Sender's address must be different from destination address */
					if (!linkaddr_cmp(&(entry->nxt_hop), &linkaddr_node_addr)) {
					    unicast_send(&uc, &(entry->nxt_hop));
					}
					else
					{
						printf("All RERR messages are transfered\n");
					}
				}
				else{
					printf("Entry Null --  cannot forward the RERR message\n");			
				}	
			}
		}
		else
		{
			printf("All RERR messages are transfered\n");
		}
	}
	/*	Data forwarding Message		*/
	else if(packetbuf_datalen() == sizeof(rcvd_data))
	{

		int uc_succ = TRUE;
		memcpy(&rcvd_data,(struct packet_data *)packetbuf_dataptr(), sizeof(rcvd_data));

		printf("unicast_recv -- Data Packet Received : src_addr - %d.%d \n  dest_addr : %d.%d  \n dest_seq_num : %d, data : %s  \n",\
					 rcvd_data.src_addr.u8[0], rcvd_data.src_addr.u8[1],rcvd_data.dest_addr.u8[0], rcvd_data.dest_addr.u8[1], rcvd_data.dest_seq_num, rcvd_data.data);

		if(!linkaddr_cmp(&(rcvd_data.dest_addr), &linkaddr_node_addr))
		{/* Enter Only if current node is not the destination */

			struct route_table_entry * entry = route_table_find(&(rcvd_data.dest_addr));
			
			if(entry != NULL){

				printf("Next hop address is : %d.%d \n", entry->nxt_hop.u8[0] ,entry->nxt_hop.u8[1] );
				 /* Copy data to the packet buffer*/
				packetbuf_copyfrom(&rcvd_data, sizeof(rcvd_data));
					
				/* linkaddr_node_addr: RIME address of the current node */
				/* Sender's address must be different from destination address */
				if (!linkaddr_cmp(&(entry->nxt_hop), &linkaddr_node_addr)) {
				    uc_succ = unicast_send(&uc, &(entry->nxt_hop));
				    printf("uc_succ : %d \n", uc_succ);
				}
				else
				{
					printf("Data Packet delivered to destination\n");
				}
			}
			else{
				printf("Entry Null");	
				uc_succ = FALSE;		
			}	
		}
		else
		{
			printf("Data Packet delivered to destination  : Data - %s \n", rcvd_data.data );
		}
		/*	Creating the RERR messages and sending	*/
		if(uc_succ==FALSE) 
		{
			printf("Link has been broken, send the RERR message\n");

			struct route_error rerr;
			
			linkaddr_copy(&(rerr.src_addr),&(rcvd_data.src_addr));
			linkaddr_copy(&(rerr.dest_addr),&(rcvd_data.dest_addr));  
			rerr.dest_seq_num = rcvd_data.dest_seq_num;

			packetbuf_copyfrom(&rerr, sizeof(rerr));
			
			/* linkaddr_node_addr: RIME address of the current node */
			/* Sender's address must be different from destination address */
			if (!linkaddr_cmp(from, &linkaddr_node_addr))
			{
			    unicast_send(&uc, from);
			}
		}
	}
	else
	{
		printf("Message with wrong packet data length is received\n");
	}
}



/*============================================================================*/
			/*AODV Code*/
/*============================================================================*/


PROCESS_THREAD(aodv_process, ev, data) {

	PROCESS_EXITHANDLER(broadcast_close(&broadcast);)
	PROCESS_EXITHANDLER(unicast_close(&uc);)
	PROCESS_BEGIN();

    /* 
     * Set up a broadcast connection
     * Arguments: channel (129) and callbacks function
     */
	broadcast_open(&broadcast, 129, &broadcast_cb);

    /* 
     * Set up a unicast connection
     * Arguments: channel (146) and callbacks function
     */
	unicast_open(&uc, 146, &unicast_cb);


	SENSORS_ACTIVATE(button_sensor);

	while (1) {
		PROCESS_WAIT_EVENT_UNTIL(ev == sensors_event && data == &button_sensor)	;

		linkaddr_t tmp_dest_addr;
		tmp_dest_addr.u8[0] = 1;
		tmp_dest_addr.u8[1] = 0;
	
		struct route_table_entry * entry = route_table_find(&(tmp_dest_addr));
		
		if(entry != NULL)
		{
			if(entry->valid == TRUE)
			{
				printf("Path to the destination(%d.%d) is already known. Send data through unicast\n", tmp_dest_addr.u8[0], tmp_dest_addr.u8[1]);
				
				struct packet_data data_sent;
				linkaddr_copy(&(data_sent.src_addr),&linkaddr_node_addr);
				linkaddr_copy(&(data_sent.dest_addr),&tmp_dest_addr);
				data_sent.dest_seq_num = entry->seq_num;
				strcpy(data_sent.data, "Chethan");

				printf("Next hop address is : %d.%d \n", entry->nxt_hop.u8[0] ,entry->nxt_hop.u8[1] );
				 /* Copy data to the packet buffer*/
				packetbuf_copyfrom(&data_sent, sizeof(data_sent));
					
				/* linkaddr_node_addr: RIME address of the current node */
				/* Sender's address must be different from destination address */
				if (!linkaddr_cmp(&(entry->nxt_hop), &linkaddr_node_addr)) {
				    unicast_send(&uc, &(entry->nxt_hop));
				}
			}
			else
			{
				/*Framing the Route Request Packet*/
				struct route_request request;
				seq_num_cntr = seq_num_cntr+1;
				linkaddr_copy(&(request.src_addr),&linkaddr_node_addr); 
				request.src_seq_num = seq_num_cntr;
				request.broadcast_id = 1;
				linkaddr_copy(&(request.dest_addr),&tmp_dest_addr); 
				request.dest_seq_num = entry->seq_num;
				request.hop_cnt = 0;

				/* Copy data to the packet buffer */
				packetbuf_copyfrom(&request,sizeof(request));
						//packetbuf_copyfrom("RREQ", 5);
				/* Send broadcast packet */
				broadcast_send(&broadcast);
				
				printf("Request sent to find %d.%d from %d.%d with broadcast_id : %d\n",\
					request.dest_addr.u8[0],request.dest_addr.u8[1],request.src_addr.u8[0],request.src_addr.u8[1],request.broadcast_id);
			}
		}
		else
		{
		
			/*Framing the Route Request Packet*/
			struct route_request request;
			seq_num_cntr = seq_num_cntr+1;
			linkaddr_copy(&(request.src_addr),&linkaddr_node_addr); 
			request.src_seq_num = seq_num_cntr;
			request.broadcast_id = 1;
			linkaddr_copy(&(request.dest_addr),&tmp_dest_addr); 
			request.dest_seq_num = 0;
			request.hop_cnt = 0;

			/* Copy data to the packet buffer */
			packetbuf_copyfrom(&request,sizeof(request));
					//packetbuf_copyfrom("RREQ", 5);
			/* Send broadcast packet */
			broadcast_send(&broadcast);
			
			printf("Request sent to find %d.%d from %d.%d with broadcast_id : %d\n",\
				request.dest_addr.u8[0],request.dest_addr.u8[1],request.src_addr.u8[0],request.src_addr.u8[1],request.broadcast_id);
		}

	}

	PROCESS_END();

}


/*-------Function Defenitions-------*/


void route_table_init(void)
{
  list_init(route_table);
  memb_init(&route_mem);
}

/*---------------------------------------------------------------------------*/
//struct route_table_entry * route_table_add( struct route_request * rreq , const linkaddr_t * nexthop  )
struct route_table_entry * route_table_add( const int valid, const linkaddr_t* dest_addr, const linkaddr_t * nexthop, const int seq_num ,const int hop_cnt,const int lifetime )
{
	struct route_table_entry *e;

	/* Avoid inserting duplicate entries. */
	e = route_table_find(dest_addr);

	if(e == NULL)
	{

		/* Allocate a new entry or reuse the oldest. */
		e = memb_alloc(&route_mem);
	    	if(e == NULL) {
	      		e = list_chop(route_table); /* Remove oldest entry. */
		}

		e->valid = valid;
		linkaddr_copy(&e->dest_addr, dest_addr);
		linkaddr_copy(&e->nxt_hop, nexthop);
		e->hop_cnt = hop_cnt + 1 ;
		e->seq_num = seq_num;
		e->lifetime = lifetime;

		printf("Adding entry to route table: dest_addr : %d.%d , nexthop : %d.%d , hop_cnt : %d , seq_num : %d , lifetime :%d\n",  
					e->dest_addr.u8[0],e->dest_addr.u8[1],e->nxt_hop.u8[0],e->nxt_hop.u8[1], e->hop_cnt , e->seq_num, e->lifetime );

		/* New entry goes first. */
		list_push(route_table, e);

	}
	else if((e != NULL) && (e->hop_cnt > hop_cnt))
	{
		if(e != NULL) {
		    list_remove(route_table, e);    
		} else {
			/* Allocate a new entry or reuse the oldest. */
			e = memb_alloc(&route_mem);
		    	if(e == NULL) {
		      		e = list_chop(route_table); /* Remove oldest entry. */
			}
		}

		e->valid = valid;
		linkaddr_copy(&e->dest_addr, dest_addr);
		linkaddr_copy(&e->nxt_hop, nexthop);
		e->hop_cnt = hop_cnt + 1 ;
		e->seq_num = seq_num;
		e->lifetime = lifetime;

		printf("Adding entry to route table: dest_addr : %d.%d , nexthop : %d.%d , hop_cnt : %d , seq_num : %d , lifetime :%d\n",  
					e->dest_addr.u8[0],e->dest_addr.u8[1],e->nxt_hop.u8[0],e->nxt_hop.u8[1], e->hop_cnt , e->seq_num, e->lifetime );

		/* New entry goes first. */
		list_push(route_table, e);
	}
	else
	{
		printf("Hop count in the current table entry is less.\n");
	}

	return e;
}
/*---------------------------------------------------------------------------*/
struct route_table_entry * route_table_find(const linkaddr_t *dest)
{
  struct route_table_entry *e;

  for(e = list_head(route_table); e != NULL; e = e->next) {
    if(linkaddr_cmp(dest, &e->dest_addr)) {
      return e;
    }
  }
  return NULL;
}

void route_table_remove(struct route_table_entry *e)
{
  list_remove(route_table, e);
  memb_free(&route_mem, e);
}

#if 0
struct route_table_entry * route_table_lookup(uip_ipaddr_t *dest)
{
  struct route_table_entry *e;

  e = route_table_lookup_any(dest);
  if(e != NULL && e->is_bad)
    return NULL;
  return e;
}
/*---------------------------------------------------------------------------*/

void
route_table_remove(struct route_table_entry *e)
{
  list_remove(route_table, e);
  memb_free(&route_mem, e);
}


void
route_table_lru(struct route_table_entry *e)
{
  if(e != list_head(route_table)) {
    list_remove(route_table, e);
    list_push(route_table, e);
  }
}
#endif
/*---------------------------------------------------------------------------*/
void route_table_delete_all(void)
{
  struct route_table_entry *e;

  while (1) {
    e = list_pop(route_table);
    if(e != NULL)
      memb_free(&route_mem, e);
    else
      break;
  }
}

