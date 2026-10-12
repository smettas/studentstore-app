import {apiRequest} from './apiClient';
export const cartApi={
 get:()=>apiRequest('/cart/'),
 add:(product_id,quantity=1)=>apiRequest('/cart/items/',{method:'POST',data:{product_id,quantity}}),
 update:(id,quantity)=>apiRequest(`/cart/items/${id}/`,{method:'PATCH',data:{quantity}}),
 remove:id=>apiRequest(`/cart/items/${id}/`,{method:'DELETE'}),
 clear:()=>apiRequest('/cart/',{method:'DELETE'}),
};
