import React from 'react';
import {ScrollView,Text} from 'react-native';
import {useAuth} from '../store/auth';
import ActionButton from '../components/ActionButton';
import {styles} from '../styles/screens/ProfileScreen.styles';
export default function ProfileScreen({navigation}) {
 const {user,isAuthenticated,signOut}=useAuth();
 return <ScrollView style={styles.container} contentContainerStyle={styles.content}><Text style={styles.title}>My profile</Text>{!isAuthenticated?<><Text style={styles.subtitle}>Browse freely. Sign in to check out or see your orders.</Text><ActionButton title="Sign in / Sign up" onPress={()=>navigation.navigate('Authentication')}/></>:<><Text style={styles.card}>Name: {user?.name||''}{'\n'}Mobile: {user?.mobile||''}{'\n'}Email: {user?.email||''}</Text><ActionButton title="My orders" onPress={()=>navigation.navigate('OrderList')}/><ActionButton title="My addresses" secondary onPress={()=>navigation.navigate('AddressList')}/><ActionButton title="Sign out" secondary onPress={signOut}/></>}</ScrollView>;
}
