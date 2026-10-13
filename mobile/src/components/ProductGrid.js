import React from 'react';
import { View } from 'react-native';
import ItemTile from './ItemTile';
export default function ProductGrid({ products, navigation }) {
  return <View style={{ flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' }}>
    {products.map(p => <ItemTile key={p.id} product={p} onPress={() => navigation.navigate('ProductDetail', { slug: p.slug })} />)}
  </View>;
}
