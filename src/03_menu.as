// =====================================================================
//  Rehauled title screen: difficulty select, continue, endless, local
//  high scores. Called from the patched initMenu().
// =====================================================================
rhDecorateMenu = function(cc)
{
   var badge = cc.createEmptyMovieClip("rhBadge",5000);
   var t = rhText(badge,"t",1,-170,0,340,60,"REHAULED",38,16733440,"center");
   badge.filters = [new flash.filters.GlowFilter(16777215,1,4,4,12,1),new flash.filters.GlowFilter(0,1,7,7,6,1),new flash.filters.DropShadowFilter(4,60,0,0.5,4,4,1,1)];
   badge._x = 470;
   badge._y = 112;
   badge._rotation = -7;
   badge.tel = 0;
   badge.onEnterFrame = function()
   {
      this.tel++;
      this._xscale = this._yscale = 100 + Math.sin(this.tel / 9) * 4;
   };
   var y0 = 204;
   if(rhHasSave())
   {
      var c = rhMenuWord(cc,"rhContinue",5001,622,y0 - 6,"CONTINUE",30,function()
      {
         rhContinueGame();
      });
      var s = rhText(cc,"rhContinueInfo",5002,330,y0 + 30,292,24,rhSaveSummary(),12,16777215,"right");
      rhOutline(s,3);
   }
   rhMenuWord(cc,"rhEndless",5003,622,422,"ENDLESS",36,function()
   {
      rhShowDifficulty("endless");
   });
   var wn = rhButton(cc,"rhNews",5005,16,428,128,26,"WHAT'S NEW",13,function()
   {
      rhShowNews();
   });
   var foot = rhText(cc,"rhFoot",5004,180,458,450,22,"Rehauled v" + _global.RH_VERSION + "  -  keys: 1-5 ammo   F fast-forward   M music",11,16777215,"right");
   rhOutline(foot,3);
   if(_global.rhPendingScore != undefined)
   {
      var ps = _global.rhPendingScore;
      _global.rhPendingScore = undefined;
      rhEnterScore(ps.score,ps.label);
   }
};

rhStartNew = function(diff, mode)
{
   _root.rhModalMC.removeMovieClip();
   rhNewGame(diff,mode);
   var target = mode == "endless" ? "overview" : "startgame";
   rhFadeTo(target);
};

rhContinueGame = function()
{
   rhLoadGame();
   rhFadeTo("overview");
};

rhFadeTo = function(label)
{
   var f = _root.attachMovie("intro_fade","intro_fade",_root.getNextHighestDepth());
   f._alpha = 0;
   f.target = label;
   f.onEnterFrame = function()
   {
      if(this._alpha < 100)
      {
         this._alpha += 10;
      }
      else
      {
         var lbl = this.target;
         root.mcControlCenter.removeMovieClip();
         _root.rhModalMC.removeMovieClip();
         this.removeMovieClip();
         root.gotoAndStop(lbl);
      }
   };
};

rhShowDifficulty = function(mode)
{
   var p = rhModal("rhModalMC",900,440,330,mode == "endless" ? "ENDLESS MODE" : "NEW GAME");
   var sub = rhText(p,"sub",11,20,56,400,24,mode == "endless" ? "Survive wave after wave. Every lost battle costs a life." : "Choose your difficulty",13,6697728,"center");
   var info = ["Sloppy enemies, gentle wind,\n1000 starting credits","The intended challenge.\nScore x1","Sharpshooters, strong wind,\nno starting money. Score x1.5"];
   var i = 0;
   while(i < 3)
   {
      var b = rhButton(p,"d" + i,20 + i,30,92 + i * 66,150,46,_global.RH_DIFF[i].name,22,function()
      {
         rhStartNew(this.diff,this.mode);
      });
      b.diff = i;
      b.mode = mode;
      var it = rhText(p,"i" + i,30 + i,192,95 + i * 66,230,44,info[i],12,6697728,"left");
      i++;
   }
   if(rhHasSave())
   {
      rhText(p,"warn",45,20,264,400,20,"Starting a new game replaces your saved game.",11,13369344,"center","Arial");
   }
   rhButton(p,"back",40,150,288,140,32,"BACK",16,function()
   {
      _root.rhModalMC.removeMovieClip();
   });
};

rhShowNews = function()
{
   var p = rhModal("rhModalMC",900,470,380,"WHAT'S NEW");
   var lines = ["Difficulty select: Easy, Normal or Hard","ENDLESS mode: random waves, 3 lives, tougher every wave","Wind changes every turn - watch the gauge up top","Smarter enemies that simulate their shots and zero in","New ammo: TRIPLE SHOT (key 4) and MEGA BOMB (key 5)","Armory upgrades: ARMOR and the AIM SCOPE path preview","Headshot and splash bonuses, slow-motion knockouts","Morning-to-dusk lighting, snow on the viking levels","Auto-save with CONTINUE, local high-score table","Keys: 1-5 pick ammo, F fast-forward, M music"];
   var i = 0;
   while(i < lines.length)
   {
      rhText(p,"b" + i,20 + i,24,60 + i * 26,24,24,"*",16,13382400,"left");
      rhText(p,"l" + i,40 + i,44,62 + i * 26,410,24,lines[i],13,6697728,"left","Arial");
      i++;
   }
   rhButton(p,"close",90,165,326,140,36,"OK",18,function()
   {
      _root.rhModalMC.removeMovieClip();
   });
};
