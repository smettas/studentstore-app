import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import HomeScreen from '../screens/HomeScreen';
import SearchScreen from '../screens/SearchScreen';
import CartScreen from '../screens/CartScreen';
import WishlistScreen from '../screens/WishlistScreen';
import ProfileScreen from '../screens/ProfileScreen';
import { ROUTES } from '../constants/routes';
import { colors } from '../constants/colors';
const Tab = createBottomTabNavigator();
export default function MainTabs() {
  return <Tab.Navigator screenOptions={{ tabBarActiveTintColor: colors.primary || '#2563eb', headerTitle: 'StudentStore' }}>
    <Tab.Screen name={ROUTES.HOME} component={HomeScreen} />
    <Tab.Screen name={ROUTES.SEARCH} component={SearchScreen} />
    <Tab.Screen name={ROUTES.CART} component={CartScreen} />
    <Tab.Screen name={ROUTES.WISHLIST} component={WishlistScreen} />
    <Tab.Screen name={ROUTES.PROFILE} component={ProfileScreen} />
  </Tab.Navigator>;
}
