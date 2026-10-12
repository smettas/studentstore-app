import React from 'react';
import { ActivityIndicator, View } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import MainTabs from './MainTabs';
import AuthStack from './AuthStack';
import { useAuth } from '../store/auth';
import { ROUTES } from '../constants/routes';
import CategoryScreen from '../screens/CategoryScreen';
import ProductListScreen from '../screens/ProductListScreen';
import ProductDetailScreen from '../screens/ProductDetailScreen';
import CheckoutScreen from '../screens/CheckoutScreen';
import PaymentScreen from '../screens/PaymentScreen';
import OrderListScreen from '../screens/OrderListScreen';
import OrderDetailScreen from '../screens/OrderDetailScreen';
import AddressListScreen from '../screens/AddressListScreen';
import AddAddressScreen from '../screens/AddAddressScreen';
const Stack = createNativeStackNavigator();
export default function RootNavigator() {
  const { loading, isAuthenticated } = useAuth();
  if (loading) return <View style={{ flex: 1, justifyContent: 'center' }}><ActivityIndicator /></View>;
  return <NavigationContainer>
    <Stack.Navigator>
      <Stack.Screen name="Shop" component={MainTabs} options={{ headerShown: false }} />
      <Stack.Screen name="Authentication" component={AuthStack} options={{ headerShown: false, presentation: 'modal' }} />
      <Stack.Screen name={ROUTES.CATEGORY} component={CategoryScreen} />
      <Stack.Screen name={ROUTES.PRODUCTS} component={ProductListScreen} />
      <Stack.Screen name={ROUTES.PRODUCT} component={ProductDetailScreen} />
      {isAuthenticated && <>
        <Stack.Screen name={ROUTES.CHECKOUT} component={CheckoutScreen} />
        <Stack.Screen name={ROUTES.PAYMENT} component={PaymentScreen} />
        <Stack.Screen name={ROUTES.ORDERS} component={OrderListScreen} />
        <Stack.Screen name={ROUTES.ORDER} component={OrderDetailScreen} />
        <Stack.Screen name={ROUTES.ADDRESSES} component={AddressListScreen} />
        <Stack.Screen name={ROUTES.ADD_ADDRESS} component={AddAddressScreen} />
      </>}
    </Stack.Navigator>
  </NavigationContainer>;
}
// Guest browsing remains available; screens should navigate to Authentication at checkout.
