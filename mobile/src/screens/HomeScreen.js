import React, { useCallback, useState } from 'react';
import { ScrollView, Text, Pressable, View, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { productApi } from '../services/productApi';
import ProductGrid from '../components/ProductGrid';
import ScreenState from '../components/ScreenState';
import { rows, errorText } from '../utils/ui';
export default function HomeScreen({ navigation }) {
  const [products, setProducts] = useState([]), [categories, setCategories] = useState([]), [levels, setLevels] = useState([]), [loading, setLoading] = useState(true), [error, setError] = useState('');
  const load = useCallback(async () => { setLoading(true); setError(''); try { const [p, c, l] = await Promise.all([productApi.list({}), productApi.categories(), productApi.studyLevels()]); setProducts(rows(p)); setCategories(rows(c)); setLevels(rows(l)); } catch(e) { setError(errorText(e)); } finally { setLoading(false); } }, []);
  useFocusEffect(useCallback(() => { load(); }, [load]));
  return <ScrollView style={{ flex: 1, backgroundColor: '#f7f9fc' }} contentContainerStyle={{ padding: 16, paddingBottom: 40 }} refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}>
    <View style={{ backgroundColor: '#1d4ed8', borderRadius: 20, padding: 22, marginBottom: 22 }}><Text style={{ color: '#bfdbfe', fontWeight: '700' }}>WELCOME TO STUDENTSTORE</Text><Text style={{ color: '#fff', fontSize: 27, fontWeight: '900', marginTop: 8 }}>Everything for your learning journey.</Text><Text style={{ color: '#dbeafe', marginTop: 8 }}>School • College • Exam essentials</Text><Pressable onPress={() => navigation.navigate('ProductList')} style={{ backgroundColor: '#fff', padding: 13, borderRadius: 10, alignSelf: 'flex-start', marginTop: 18 }}><Text style={{ color: '#1d4ed8', fontWeight: '800' }}>Shop all products  →</Text></Pressable></View>
    <Text style={{ fontSize: 20, fontWeight: '800', color: '#0f172a', marginBottom: 12 }}>Shop by category</Text>
    <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 20 }}>{categories.map(c => <Pressable key={c.id} onPress={() => navigation.navigate('ProductList', { category: c.slug })} style={{ paddingVertical: 12, paddingHorizontal: 14, backgroundColor: '#fff', borderWidth: 1, borderColor: '#e2e8f0', borderRadius: 12 }}><Text style={{ fontWeight: '600', color: '#334155' }}>{c.name}</Text></Pressable>)}</View>
    <Text style={{ fontSize: 20, fontWeight: '800', color: '#0f172a', marginBottom: 12 }}>Shop by study level</Text><View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 20 }}>{levels.map(l => <Pressable key={l.id} onPress={() => navigation.navigate('ProductList', { study_level: l.slug })} style={{ padding: 11, backgroundColor: '#eaf1ff', borderRadius: 10 }}><Text style={{ color: '#1d4ed8', fontWeight: '700' }}>{l.name}</Text></Pressable>)}</View>
    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 }}><Text style={{ fontSize: 20, fontWeight: '800', color: '#0f172a' }}>Explore products</Text><Text onPress={() => navigation.navigate('ProductList')} style={{ color: '#2563eb', fontWeight: '700' }}>View all →</Text></View>
    <ScreenState loading={loading && !products.length} error={error} onRetry={load} empty={!loading && !products.length ? 'No products available.' : ''}/><ProductGrid products={products.slice(0, 12)} navigation={navigation}/>
  </ScrollView>;
}
