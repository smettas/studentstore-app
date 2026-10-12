import React from 'react';
import { Image, Pressable, Text, View } from 'react-native';
import { money, priceOf } from '../utils/ui';
export default function ItemTile({product, onPress}) {
 const image = product?.primary_image?.image_url || product?.images?.[0]?.image_url;
 return <Pressable onPress={onPress} style={{flexDirection:'row',backgroundColor:'#fff',borderRadius:12,padding:12,marginBottom:10,alignItems:'center'}}>
 {image ? <Image source={{uri:image}} style={{width:76,height:76,borderRadius:8,marginRight:12}}/> : <View style={{width:76,height:76,backgroundColor:'#e9eef5',borderRadius:8,marginRight:12}}/>}
 <View style={{flex:1}}><Text style={{fontWeight:'700',fontSize:15}} numberOfLines={2}>{product?.name}</Text><Text style={{marginTop:5}}>{money(priceOf(product))}</Text><Text style={{color:'#667085'}}>{product?.in_stock === false ? 'Out of stock' : product?.brand?.name || ''}</Text></View></Pressable>;
}
