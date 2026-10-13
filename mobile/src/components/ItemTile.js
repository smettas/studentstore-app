import React, { useState } from 'react';
import { Image, Pressable, Text, View } from 'react-native';
import { money, priceOf } from '../utils/ui';
import { resolveImageUrl } from '../utils/imageUrl';
export default function ItemTile({ product, onPress, compact = false }) {
  const [broken, setBroken] = useState(false);
  const uri = resolveImageUrl(product?.primary_image?.image_url || product?.images?.[0]?.image_url);
  const price = Number(priceOf(product));
  const mrp = Number(product?.price || 0);
  const discount = mrp > price && price > 0 ? Math.round((mrp - price) / mrp * 100) : 0;
  return <Pressable onPress={onPress} accessibilityRole="button" style={{ width: compact ? '100%' : '48.5%', backgroundColor: '#fff', borderRadius: 16, borderWidth: 1, borderColor: '#e5eaf2', marginBottom: 12, overflow: 'hidden', elevation: 1 }}>
    <View style={{ height: 190, backgroundColor: '#f4f7fb', alignItems: 'center', justifyContent: 'center' }}>
      {uri && !broken ? <Image source={{ uri }} resizeMode="conver" onError={() => setBroken(true)} style={{ width: '100%', height: 190 }} /> : <Text style={{ color: '#94a3b8', fontSize: 12 }}>Image unavailable</Text>}
      {!product?.in_stock && <View style={{ position: 'absolute', top: 8, left: 8, backgroundColor: '#334155', borderRadius: 6, paddingHorizontal: 7, paddingVertical: 4 }}><Text style={{ color: '#fff', fontSize: 10, fontWeight: '700' }}>OUT OF STOCK</Text></View>}
    </View>
    <View style={{ padding: 11, minHeight: 117 }}>
      <Text numberOfLines={1} style={{ color: '#64748b', fontSize: 11, fontWeight: '700', textTransform: 'uppercase' }}>{product?.brand?.name?.toLowerCase().includes('unbranded')
  ? product?.category?.name
  : product?.brand?.name || product?.category?.name || 'StudentStore'}</Text>
      <Text numberOfLines={2} style={{ fontSize: 13, fontWeight: '700', color: '#0f172a', marginTop: 5, minHeight: 35 }}>{product?.name}</Text>
      <View style={{ flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', gap: 5, marginTop: 5 }}><Text style={{ fontSize: 16, fontWeight: '800', color: '#0f172a' }}>{money(price)}</Text>{discount > 0 && <Text style={{ color: '#94a3b8', textDecorationLine: 'line-through', fontSize: 11 }}>{money(mrp)}</Text>}</View>
      {discount > 0 && <Text style={{ color: '#15803d', fontSize: 11, fontWeight: '700', marginTop: 3 }}>{discount}% off</Text>}
    </View>
  </Pressable>;
}
