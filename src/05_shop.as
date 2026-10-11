// =====================================================================
//  Rehauled shop: extra items next to the original rocket / grenade /
//  raft upgrade buttons. Rebuilt every time initTussenscherm() runs.
// =====================================================================
_global.RH_SHOP = [{id:"triple",name:"TRIPLE SHOT",desc:"3 snowballs at once",cost:[400],max:5,key:"triples"},{id:"mega",name:"MEGA BOMB",desc:"huge blast, blows up on impact",cost:[1100],max:3,key:"megas"},{id:"armor",name:"ARMOR",desc:"crew takes less damage",cost:[1000,2000,3000],max:3,key:"armor",lvl:true},{id:"scope",name:"AIM SCOPE",desc:"shows your shot's path",cost:[800,1600,2400],max:3,key:"scope",lvl:true}];

rhShopItem = function(id)
{
   var i = 0;
   while(i < _global.RH_SHOP.length)
   {
      if(_global.RH_SHOP[i].id == id)
      {
         return _global.RH_SHOP[i];
      }
      i++;
   }
   return null;
};

rhShopCost = function(it)
{
   var have = rhNum(_global.saveProgress[it.key]);
   if(it.lvl == true)
   {
      return it.cost[Math.min(have,it.cost.length - 1)];
   }
   return it.cost[0];
};

rhBuy = function(id)
{
   var it = rhShopItem(id);
   var sp = _global.saveProgress;
   var have = rhNum(sp[it.key]);
   var cost = rhShopCost(it);
   if(have >= it.max || cost > sp.money)
   {
      return undefined;
   }
   sp[it.key] = have + 1;
   sp.money -= cost;
   speelSimpelSFX("draw_weapon");
   initTussenscherm(true);
   rhSaveGame();
};

rhShopExtras = function()
{
   var ts = hud.tussenscherm;
   if(ts == undefined)
   {
      return undefined;
   }
   ts.rhShop.removeMovieClip();
   var s = ts.createEmptyMovieClip("rhShop",5000);
   s._x = 10;
   s._y = 298;
   var w = 314;
   rhRect(s,0,0,w,146,14,1714764,62,16777215,60);
   var hdr = rhText(s,"hdr",1,10,3,w - 20,22,"REHAULED ARMORY",14,16776960,"left");
   rhOutline(hdr,3);
   var sp = _global.saveProgress;
   var i = 0;
   while(i < _global.RH_SHOP.length)
   {
      var it = _global.RH_SHOP[i];
      var cx = 6 + i % 2 * 153;
      var cy = 27 + Math.floor(i / 2) * 58;
      var have = rhNum(sp[it.key]);
      var cost = rhShopCost(it);
      var cell = s.createEmptyMovieClip("c" + i,10 + i);
      cell._x = cx;
      cell._y = cy;
      rhRect(cell,0,0,149,55,8,0,22);
      var nm = rhText(cell,"n",1,4,1,145,20,it.name,13,16777215,"left");
      rhOutline(nm,2);
      rhText(cell,"d",2,4,18,145,16,it.desc,9,15658734,"left","Arial");
      var st = rhText(cell,"st",3,4,34,70,20,it.lvl == true ? "LV " + have + "/" + it.max : have + " / " + it.max,12,16776960,"left");
      rhOutline(st,2);
      var canBuy = have < it.max && cost <= sp.money;
      var b = rhButton(cell,"b",4,72,30,72,23,have >= it.max ? "MAX" : String(cost),12,function()
      {
         rhBuy(this.itemId);
      });
      b.itemId = it.id;
      if(!canBuy)
      {
         b.enabled = false;
         b._alpha = 45;
      }
      i++;
   }
   if(rhIsEndless())
   {
      var lv = rhText(ts,"rhLives",5001,14,272,300,24,"WAVE " + _global.RH.wave + "   LIVES " + Math.max(0,_global.progress.lives),16,16776960,"left");
      rhOutline(lv,3);
   }
};
