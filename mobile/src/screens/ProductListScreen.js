import React, { useEffect, useState } from 'react';
import { ScrollView, Text, View, TextInput, Pressable, ActivityIndicator } from 'react-native';
import { productApi } from '../services/productApi';
import ProductGrid from '../components/ProductGrid';
import ScreenState from '../components/ScreenState';
import { rows, errorText } from '../utils/ui';
const chip = { paddingVertical: 9, paddingHorizontal: 12, borderRadius: 10, borderWidth: 1, borderColor: '#dbe3f0', backgroundColor: '#fff', marginRight: 7, marginBottom: 7 };
export default function ProductListScreen({ route, navigation }) {
  const [products, setProducts] = useState([]), [loading, setLoading] = useState(false), [error, setError] = useState(''), [min, setMin] = useState(''), [max, setMax] = useState(''), [brand, setBrand] = useState(''), [sort, setSort] = useState('newest'), [page, setPage] = useState(1), [next, setNext] = useState(false), [showFilters, setShowFilters] = useState(false), [brands, setBrands] = useState([]);
  const filters = route.params || {};
  useEffect(() => { productApi.brands().then(v => setBrands(rows(v))).catch(() => {}); }, []);
  async function load(pageNum = 1, selectedSort = sort, selectedBrand = brand) { if (loading) return; setLoading(true); setError(''); try { const result = await productApi.list({ ...filters, min_price: min, max_price: max, brand: selectedBrand, ordering: selectedSort, page: pageNum }); setProducts(old => pageNum === 1 ? rows(result) : [...old, ...rows(result)]); setNext(Boolean(result?.next)); setPage(pageNum); } catch(e) { setError(errorText(e)); } finally { setLoading(false); } }
  useEffect(() => { load(1); }, [route.params]);
  const input = { backgroundColor: '#fff', borderWidth: 1, borderColor: '#dbe3f0', borderRadius: 10, padding: 12, flex: 1, minWidth: 110 };
  return <ScrollView style={{ flex: 1, backgroundColor: '#f7f9fc' }} contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
    <Text style={{ fontSize: 23, fontWeight: '900', color: '#0f172a' }}>Explore products</Text><Text style={{ color: '#64748b', marginTop: 4, marginBottom: 14 }}>Discover stationery and study essentials</Text>
    <View style={{ flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center' }}>{[['Newest','newest'],['Price ↑','price_asc'],['Price ↓','price_desc'],['Name','name']].map(([label,value]) => <Pressable key={value} style={[chip,sort===value && { backgroundColor: '#dbeafe', borderColor: '#2563eb' }]} onPress={() => { setSort(value); load(1,value); }}><Text style={{ color: '#1d4ed8', fontWeight: '700' }}>{label}</Text></Pressable>)}</View>
    <Pressable onPress={() => setShowFilters(v => !v)} style={{ paddingVertical: 12 }}><Text style={{ color: '#1d4ed8', fontWeight: '800' }}>{showFilters ? 'Hide filters ▲' : 'Filter by brand and price ▼'}</Text></Pressable>
    {showFilters && <View style={{ backgroundColor: '#fff', borderRadius: 14, padding: 12, marginBottom: 12 }}><Text style={{ fontWeight: '700', marginBottom: 8 }}>Price range (₹)</Text><View style={{ flexDirection: 'row', gap: 8 }}><TextInput placeholder="Minimum" keyboardType="numeric" value={min} onChangeText={setMin} style={input}/><TextInput placeholder="Maximum" keyboardType="numeric" value={max} onChangeText={setMax} style={input}/></View><Text style={{ fontWeight: '700', marginTop: 12, marginBottom: 8 }}>Brands</Text><View style={{ flexDirection: 'row', flexWrap: 'wrap' }}><Pressable style={[chip,!brand && { backgroundColor: '#dbeafe' }]} onPress={() => setBrand('')}><Text>All</Text></Pressable>{brands.map(b => <Pressable key={b.id} style={[chip,brand===b.slug && { backgroundColor: '#dbeafe' }]} onPress={() => setBrand(b.slug)}><Text>{b.name}</Text></Pressable>)}</View><Pressable onPress={() => load(1)} style={{ backgroundColor: '#2563eb', padding: 13, borderRadius: 10, alignItems: 'center' }}><Text style={{ color: '#fff', fontWeight: '800' }}>Apply filters</Text></Pressable></View>}
    <ScreenState loading={loading && !products.length} error={error} onRetry={() => load(1)} empty={!loading && !products.length ? 'No matching products.' : ''}/><ProductGrid products={products} navigation={navigation}/>
    {next && <Pressable disabled={loading} onPress={() => load(page+1)} style={{ backgroundColor: '#e0ebff', borderRadius: 12, padding: 14, alignItems: 'center' }}>{loading ? <ActivityIndicator/> : <Text style={{ color: '#1d4ed8', fontWeight: '800' }}>Load more products</Text>}</Pressable>}
  </ScrollView>;
}
