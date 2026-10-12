import {apiRequest} from './apiClient';
export const wishlistApi={
 get:()=>apiRequest('/wishlist/'),
 add:product_id=>apiRequest('/wishlist/',{method:'POST',data:{product_id}}),
 remove:id=>apiRequest(`/wishlist/items/${id}/`,{method:'DELETE'}),
};
