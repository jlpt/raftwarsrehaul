// =====================================================================
//  RAFT WARS: REHAULED
//  Core: state, difficulty, save games, small helpers.
//  Appended after the original frame-4 script, so everything here can
//  use (and wrap) the original game functions.
// =====================================================================
_global.RH_VERSION = "1.0";

// Difficulty presets.
//   aiErr     scales the enemy's aiming error (bigger = sloppier)
//   aiWind    how much of the wind the enemy compensates for
//   toPlayer  damage multiplier for hits on your crew
//   toEnemy   damage multiplier for hits on the enemy
//   windMul   wind strength multiplier
//   credits   starting credits, lives = endless-mode lives
//   scoreMul  final score multiplier
_global.RH_DIFF = [{name:"EASY",aiErr:1.7,aiWind:0.35,toPlayer:0.7,toEnemy:1.3,windMul:0.6,credits:1000,lives:5,scoreMul:0.75},{name:"NORMAL",aiErr:1,aiWind:0.75,toPlayer:1,toEnemy:1,windMul:1,credits:300,lives:3,scoreMul:1},{name:"HARD",aiErr:0.62,aiWind:1,toPlayer:1.2,toEnemy:0.85,windMul:1.25,credits:0,lives:2,scoreMul:1.5}];

// Maximum wind per campaign level (pixels/frame^2 added to projectile vx).
_global.RH_WIND = [0,0.006,0.012,0.016,0.02,0.024,0.028,0.032,0.036,0.04,0.045];

rhInit = function()
{
   if(_global.RH == undefined)
   {
      _global.RH = {diff:1,mode:"campaign",wave:1,lastLevel:0};
   }
   if(_global.RHset == undefined)
   {
      _global.RHset = {ff:false};
      var so = rhSO();
      if(so.data.settings != undefined)
      {
         _global.RHset.ff = so.data.settings.ff == true;
         _global.quiet = so.data.settings.quiet == true;
      }
   }
   if(_global.rhKeys == undefined)
   {
      _global.rhKeys = {};
      _global.rhKeys.onKeyDown = function()
      {
         rhOnKey(Key.getCode(),Key.getAscii());
      };
      Key.addListener(_global.rhKeys);
   }
};

rhD = function()
{
   var d = _global.RH.diff;
   if(d == undefined || d < 0 || d > 2)
   {
      d = 1;
   }
   return _global.RH_DIFF[d];
};

rhIsEndless = function()
{
   return _global.RH.mode == "endless";
};

// ---------------------------------------------------------------- save
rhSO = function()
{
   if(_global.rhSOcache == undefined)
   {
      _global.rhSOcache = SharedObject.getLocal("raftwars_rehauled","/");
   }
   return _global.rhSOcache;
};

rhCopy = function(o)
{
   var c = {};
   var k;
   for(k in o)
   {
      if(typeof o[k] != "function" && typeof o[k] != "movieclip")
      {
         c[k] = o[k];
      }
   }
   return c;
};

rhSaveSettings = function()
{
   var so = rhSO();
   so.data.settings = {ff:_global.RHset.ff,quiet:_global.quiet};
   so.flush();
};

rhSaveGame = function()
{
   if(_global.twoPlayer == true || _global.progress == undefined || _global.inGame != true)
   {
      return undefined;
   }
   var so = rhSO();
   so.data.save = {progress:rhCopy(_global.progress),sp:rhCopy(_global.saveProgress),rh:rhCopy(_global.RH),stamp:new Date().getTime()};
   so.flush();
};

rhHasSave = function()
{
   var s = rhSO().data.save;
   return s != undefined && s.progress != undefined && s.progress.level != undefined;
};

rhLoadGame = function()
{
   var s = rhSO().data.save;
   _global.progress = rhCopy(s.progress);
   var k;
   for(k in s.sp)
   {
      _global.saveProgress[k] = s.sp[k];
   }
   _global.RH = rhCopy(s.rh);
   _global.inGame = true;
   _global.twoPlayer = false;
   _global.doeInstructions = false;
};

rhClearSave = function()
{
   var so = rhSO();
   delete so.data.save;
   so.flush();
};

rhSaveSummary = function()
{
   var s = rhSO().data.save;
   var d = _global.RH_DIFF[s.rh.diff].name;
   if(s.rh.mode == "endless")
   {
      return "ENDLESS - WAVE " + s.rh.wave + " - " + d;
   }
   var lv = s.progress.level;
   if(lv > 11)
   {
      lv = 11;
   }
   return "LEVEL " + lv + " - " + d;
};

// ------------------------------------------------------------ new game
rhNewGame = function(diff, mode)
{
   _global.RH = {diff:diff,mode:mode,wave:1,lastLevel:0};
   var D = rhD();
   _global.progress = {level:1,lives:D.lives,points:0,tries:0};
   _global.inGame = true;
   _global.twoPlayer = false;
   _global.doeInstructions = mode != "endless";
   var sp = _global.saveProgress;
   sp.grenades = 0;
   sp.rockets = 0;
   sp.triples = 0;
   sp.megas = 0;
   sp.armor = 0;
   sp.scope = 0;
   sp.money = D.credits;
   sp.raftUpgrade = 1;
   if(mode == "endless")
   {
      // endless runs start a bit equipped, the waves get rough quickly
      sp.grenades = 1;
      sp.rockets = 1;
      sp.money += 600;
      _global.progress.level = rhRandomLevel();
   }
   rhSaveGame();
};

rhRandomLevel = function()
{
   var l = 1 + random(10);
   if(l == _global.RH.lastLevel)
   {
      l = l % 10 + 1;
   }
   _global.RH.lastLevel = l;
   return l;
};

// ------------------------------------------------------------- helpers
rhIndexOf = function(arr, item)
{
   var i = 0;
   while(i < arr.length)
   {
      if(arr[i] == item)
      {
         return i;
      }
      i++;
   }
   return -1;
};

rhClamp = function(v, lo, hi)
{
   if(v < lo)
   {
      return lo;
   }
   if(v > hi)
   {
      return hi;
   }
   return v;
};

rhNum = function(v)
{
   if(v == undefined || isNaN(v))
   {
      return 0;
   }
   return Number(v);
};

rhOnKey = function(code, ascii)
{
   if(code == 70)
   {
      // F: fast-forward toggle
      _global.RHset.ff = !_global.RHset.ff;
      rhSaveSettings();
      rhUpdateHud();
      return undefined;
   }
   if(code == 77)
   {
      // M: music toggle (same as the note button)
      if(_global.quiet == false)
      {
         stopLoop();
         _global.quiet = true;
         _global.loopPlaying = "";
      }
      else
      {
         _global.quiet = false;
         if(_global.inGame == true && game.tussenscherm != true && main != undefined)
         {
            playLoop("loop");
         }
         else
         {
            playLoop("menuloop");
         }
      }
      if(cannon.loopBtn != undefined)
      {
         cannon.loopBtn.red._visible = _global.quiet;
      }
      rhSaveSettings();
      return undefined;
   }
   if(code >= 49 && code <= 53)
   {
      rhSelectAmmo(code - 48);
   }
};
