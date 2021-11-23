/*
 * Generated by asn1c-0.9.29 (http://lionet.info/asn1c)
 * From ASN.1 module "CPM-PDU-Descriptions"
 * 	found in "asn1/TR103562v211.asn"
 * 	`asn1c -fcompound-names -fincludes-quoted -no-gen-example -R`
 */

#ifndef	_OtherSublassType_H_
#define	_OtherSublassType_H_


#include "asn_application.h"

/* Including external dependencies */
#include "NativeInteger.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Dependencies */
typedef enum OtherSublassType {
	OtherSublassType_unknown	= 0,
	OtherSublassType_roadSideUnit	= 1
} e_OtherSublassType;

/* OtherSublassType */
typedef long	 OtherSublassType_t;

/* Implementation */
extern asn_per_constraints_t asn_PER_type_OtherSublassType_constr_1;
extern asn_TYPE_descriptor_t asn_DEF_OtherSublassType;
asn_struct_free_f OtherSublassType_free;
asn_struct_print_f OtherSublassType_print;
asn_constr_check_f OtherSublassType_constraint;
ber_type_decoder_f OtherSublassType_decode_ber;
der_type_encoder_f OtherSublassType_encode_der;
xer_type_decoder_f OtherSublassType_decode_xer;
xer_type_encoder_f OtherSublassType_encode_xer;
oer_type_decoder_f OtherSublassType_decode_oer;
oer_type_encoder_f OtherSublassType_encode_oer;
per_type_decoder_f OtherSublassType_decode_uper;
per_type_encoder_f OtherSublassType_encode_uper;

#ifdef __cplusplus
}
#endif

#endif	/* _OtherSublassType_H_ */
#include "asn_internal.h"
