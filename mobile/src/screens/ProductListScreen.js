import React,{useEffect,useState} from 'react';
import {ScrollView,Text,View} from 'react-native';
import {productApi} from '../services/productApi';
import ItemTile from '../components/ItemTile';
import ScreenState from '../components/ScreenState';
import FormField from '../components/FormField';
import ActionButton from '../components/ActionButton';
import {rows,errorText} from '../utils/ui';
import {styles} from '../styles/screens/ProductListScreen.styles';
export default function ProductListScreen({route,navigation}) {
 const [products,setProducts]=useState([]),[loading,setLoading]=useState(false),[error,setError]=useState('');
 const [min,setMin]=useState(''),[max,setMax]=useState(''),[brand,setBrand]=useState(''),[kind,setKind]=useState(''),[sort,setSort]=useState(''),[page,setPage]=useState(1),[next,setNext]=useState(false);
 const filters=route.params||{};
 async function load(pageNum=1){setLoading(true);setError('');try{const result=await productApi.list({...filters,min_price:min,max_price:max,brand,product_type:kind,ordering:sort,page:pageNum});setProducts(old=>pageNum===1?rows(result):[...old,...rows(result)]);setNext(Boolean(result?.next));setPage(pageNum);}catch(e){setError(errorText(e));}finally{setLoading(false);}}
 useEffect(()=>{load(1);},[route.params]);
 return <ScrollView style={styles.container} contentContainerStyle={styles.content}><Text style={styles.title}>Products</Text><FormField label="Minimum price" keyboardType="numeric" value={min} onChangeText={setMin}/><FormField label="Maximum price" keyboardType="numeric" value={max} onChangeText={setMax}/><FormField label="Brand slug (optional)" value={brand} onChangeText={setBrand}/><FormField label="Product type (optional)" value={kind} onChangeText={setKind}/><View style={styles.row}><ActionButton title="Price: low first" secondary onPress={()=>setSort('price_asc')}/><ActionButton title="Price: high first" secondary onPress={()=>setSort('price_desc')}/></View><ActionButton title="Apply filters" onPress={()=>load(1)}/><ScreenState loading={loading && !products.length} error={error} onRetry={()=>load(1)} empty={!loading&&!products.length?'No matching products.':''}/>{products.map(p=><ItemTile key={p.id} product={p} onPress={()=>navigation.navigate('ProductDetail',{slug:p.slug})}/>)}{next?<ActionButton title="Load more" loading={loading} onPress={()=>load(page+1)}/>:null}</ScrollView>;
}
