import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import HomeScreen from '../screens/HomeScreen';
import SearchScreen from '../screens/SearchScreen';
import CartScreen from '../screens/CartScreen';
import WishlistScreen from '../screens/WishlistScreen';
import ProfileScreen from '../screens/ProfileScreen';
import { ROUTES } from '../constants/routes';
const Tab = createBottomTabNavigator();
const icons = { Home: ['home','home-outline'], Search: ['search','search-outline'], Cart: ['cart','cart-outline'], Wishlist: ['heart','heart-outline'], Profile: ['person','person-outline'] };
export default function MainTabs() {
 return <Tab.Navigator screenOptions={({route}) => ({ headerTitle: 'StudentStore', headerTitleStyle: { fontWeight: '800' }, tabBarActiveTintColor: '#2563eb', tabBarInactiveTintColor: '#64748b', tabBarStyle: { height: 62, paddingBottom: 7, paddingTop: 5 }, tabBarIcon: ({color,size,focused}) => <Ionicons name={(icons[route.name] || icons.Home)[focused ? 0 : 1]} size={size} color={color}/> })}>
  <Tab.Screen name={ROUTES.HOME} component={HomeScreen}/><Tab.Screen name={ROUTES.SEARCH} component={SearchScreen}/><Tab.Screen name={ROUTES.CART} component={CartScreen}/><Tab.Screen name={ROUTES.WISHLIST} component={WishlistScreen}/><Tab.Screen name={ROUTES.PROFILE} component={ProfileScreen}/>
 </Tab.Navigator>;
}
