var locations = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad"];

locations.forEach(function(loc) {
  print("\n=== LOCATION: " + loc + " ===");
  
  // Get users from this location
  var userIds = db.users.find({location: loc}).map(u => u.user_id);
  print("Users: " + userIds.length);
  
  // Get interactions for these users
  var pipeline = [
    { $match: {user_id: {$in: userIds}} },
    { $group: {
        _id: "$product_id", 
        views: {
          $sum: {$cond: [{$eq: ["$interaction_type", "view"]}, 1, 0]}
        },
        cart_adds: {
          $sum: {$cond: [{$eq: ["$interaction_type", "add_to_cart"]}, 1, 0]}
        },
        purchases: {
          $sum: {$cond: [{$eq: ["$interaction_type", "purchase"]}, 1, 0]}
        },
        score: {
          $sum: {
            $switch: {
              branches: [
                { case: {$eq: ["$interaction_type", "view"]}, then: 1 },
                { case: {$eq: ["$interaction_type", "add_to_cart"]}, then: 3 },
                { case: {$eq: ["$interaction_type", "purchase"]}, then: 5 }
              ],
              default: 0
            }
          }
        }
      }
    },
    { $sort: {score: -1} },
    { $limit: 5 }
  ];
  
  var topProducts = db.interactions.aggregate(pipeline).toArray();
  
  // Get product names
  topProducts.forEach(function(p) {
    var product = db.products.findOne({product_id: p._id});
    if (product) {
      print(product.product_name + " (Score: " + p.score + ")");
    }
  });
});