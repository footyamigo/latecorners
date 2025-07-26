# 📊 COMPLETE STATISTICS BREAKDOWN - CORNER BETTING SYSTEM

## 🎯 **TIER 1: CORE CORNER PREDICTION STATS** ⭐⭐⭐

### **Type 34: Corners** 
- **Weight**: `corners_total × 5` (highest weight)
- **Availability**: 100% of matches
- **Usage**: Direct indicator - existing corners predict future corners
- **Optimal Range**: 6+ total corners = high activity match
- **Why Critical**: Past corner frequency is the strongest predictor of future corners

### **Type 49: Shots Inside Box** ⭐ PREMIUM GAME CHANGER
- **Weight**: `shots_inside × 4 + inside_ratio × 20`
- **Availability**: 0% lower leagues, 100% premium leagues
- **Usage**: Teams taking shots in the box are much more likely to win corners
- **Optimal Range**: 8+ inside shots OR >40% inside ratio
- **Why Critical**: Inside box shots often result in blocked shots → corners

### **Type 60: Crosses** ⭐ PREMIUM GAME CHANGER  
- **Weight**: `crosses × 2`
- **Availability**: 0% lower leagues, 100% premium leagues
- **Usage**: Crosses directly correlate with corner opportunities
- **Optimal Range**: 20+ crosses = excellent corner potential
- **Why Critical**: Failed crosses frequently result in corners

---

## 🔥 **TIER 2: ATTACKING PRESSURE INDICATORS** ⭐⭐

### **Type 44: Dangerous Attacks**
- **Weight**: `dangerous_attacks × 0.3`
- **Availability**: 100% of matches
- **Usage**: Measures attacking intensity and pressure
- **Optimal Range**: 40+ dangerous attacks = high pressure
- **Why Important**: High attacking pressure leads to more set pieces

### **Type 51: Offsides** 
- **Weight**: `offsides × 4` (high weight for small numbers)
- **Availability**: 60% of matches  
- **Usage**: Indicates aggressive attacking play
- **Optimal Range**: 3+ offsides = very aggressive attacking
- **Why Important**: Teams pushing forward aggressively create more corner situations

### **Type 42: Shots Total**
- **Weight**: `shots_total × 1.5` (fallback when Type 49 unavailable)
- **Availability**: 100% of matches
- **Usage**: Overall attacking activity measure
- **Optimal Range**: 15+ total shots = active attacking
- **Why Important**: More shots = more blocked shots = more corners

---

## ⚡ **TIER 3: SET PIECE & TEMPO INDICATORS** ⭐

### **Type 56: Free Kicks**
- **Weight**: `free_kicks × 0.8`
- **Availability**: 60% of matches
- **Usage**: Free kicks in final third often lead to corners
- **Optimal Range**: 8+ free kicks = high fouling/pressure
- **Why Useful**: Free kicks create corner opportunities when defended

### **Type 55: Throw Ins** 
- **Weight**: `throw_ins × 0.4`
- **Availability**: 40% of matches
- **Usage**: Indicates ball going out of play frequently
- **Optimal Range**: 15+ throw ins = active sideline play
- **Why Useful**: High throw-in count suggests active attacking down flanks

### **Type 43: Attacks**
- **Weight**: `attacks × 0.1` (large numbers, scaled down)
- **Availability**: 100% of matches
- **Usage**: Total attacking actions
- **Optimal Range**: 80+ attacks = very active match
- **Why Useful**: More attacks = more opportunities for corners

---

## 📈 **TIER 4: POSSESSION & CONTROL STATS**

### **Type 45: Ball Possession %**
- **Weight**: `abs(home_possession - away_possession) × 0.2`
- **Availability**: 60% of matches
- **Usage**: Possession imbalance creates pressure
- **Optimal Range**: >65% vs <35% = significant imbalance
- **Why Useful**: Dominant possession often leads to sustained pressure

### **Type 41: Shots Off Target**
- **Weight**: Used in shot location calculations
- **Availability**: 100% of matches  
- **Usage**: Combined with total shots for analysis
- **Why Useful**: Off-target shots can lead to corners if they're wide/high

---

## 🆕 **TIER 5: PREMIUM LEAGUE EXCLUSIVE STATS**

### **Type 53: Yellow Cards** (Premium leagues)
- **Weight**: Pressure indicator
- **Availability**: Premium leagues only
- **Usage**: Indicates game intensity and fouling
- **Why Useful**: High-card games often have more attacking pressure

### **Type 62: Fouls** (Premium leagues)  
- **Weight**: Pressure and set piece indicator
- **Availability**: Premium leagues only
- **Usage**: More fouls = more free kicks = more corner opportunities
- **Why Useful**: Fouling indicates defensive pressure

### **Type 27264: Successful Long Passes** (Top-tier leagues)
- **Weight**: Advanced attacking indicator
- **Availability**: Top-tier leagues only
- **Usage**: Long ball strategy can create corner situations
- **Why Useful**: Failed long passes often result in corners

---

## 🎯 **SCORING FORMULA BREAKDOWN**

### **Core Formula**:
```
Corner Score = (corners × 5) + (shots_inside × 4) + (crosses × 2)
Shot Score = (inside_ratio × 20) + (shots_total × 1.5) [fallback]
Pressure Score = (dangerous_attacks × 0.3) + (offsides × 4) + (free_kicks × 0.8) + (throw_ins × 0.4)
Base Score = Corner Score + Shot Score + Pressure Score
Quality Multiplier = 1 + (quality_score / 200)
FINAL SCORE = Base Score × Quality Multiplier
```

### **Weight Justification**:
- **Corners (×5)**: Strongest historical predictor
- **Shots Inside Box (×4)**: High correlation with corner creation  
- **Offsides (×4)**: Small numbers but strong indicator of attacking aggression
- **Crosses (×2)**: Direct corner correlation
- **Inside Ratio (×20)**: Percentage bonus for shot location accuracy

---

## 📊 **STATISTICAL AVAILABILITY BY LEAGUE TIER**

### **PREMIUM TIER** (Quality Score 120-140+)
```
✅ ALL Tier 1 stats available (34, 49, 60)
✅ ALL Tier 2 stats available (44, 51, 42)  
✅ ALL Tier 3 stats available (56, 55, 43)
✅ ALL Tier 4 stats available (45, 41)
✅ Most Tier 5 stats available (53, 62, 27264)
```

### **STANDARD TIER** (Quality Score 40-80)
```
✅ Core stats: 34, 42, 44, 43, 41
✅ Some pressure stats: 51, 56, 55
⚠️ Possession: 45 (60% availability)
❌ NO premium stats: 49, 60
❌ NO exclusive stats: 53, 62, 27264
```

### **LOW TIER** (Quality Score 0-40)
```
⚠️ Basic stats: 34, 42 (sometimes missing)
❌ Most advanced stats unavailable
❌ Poor data quality overall
```

---

## 💡 **KEY INSIGHTS FOR CORNER PREDICTION**

### **Most Predictive Combinations**:
1. **High Corners + High Inside Shots**: Nearly guaranteed more corners
2. **High Crosses + Dangerous Attacks**: Sustained attacking pressure
3. **High Offsides + Possession Imbalance**: Aggressive attacking strategy
4. **High Free Kicks + Throw Ins**: Physical, intense match tempo

### **Red Flags (Avoid)**:
- Low corners (<3) + Low shots inside box (<3) = Poor corner potential
- No premium stats available + Low quality score = Unreliable predictions
- Very low attacking stats across all categories = Defensive match

### **Golden Signals (Strong Buy)**:
- 6+ corners + 8+ inside shots + 20+ crosses = Premium opportunity
- Premium league + Quality score >120 + High activity = Maximum confidence
- Late game (75+ min) + Sustained pressure = Ideal timing

---

## 🎯 **STAT PRIORITY FOR CORNER BETTING**

### **Priority 1 (Must Have)**:
- Type 34 (Corners) - Foundation of all predictions
- Type 42 (Shots Total) - Basic attacking measure
- Type 44 (Dangerous Attacks) - Pressure indicator

### **Priority 2 (Highly Valuable)**:
- Type 49 (Shots Inside Box) - Game changer when available
- Type 60 (Crosses) - Direct corner correlation
- Type 51 (Offsides) - Attacking intensity

### **Priority 3 (Nice to Have)**:
- Type 45 (Possession %) - Control measure
- Type 56 (Free Kicks) - Set piece opportunities
- Type 55 (Throw Ins) - Tempo indicator

### **Priority 4 (Bonus)**:
- All other premium/exclusive stats - Enhance accuracy

This breakdown shows exactly how our system transforms raw match statistics into actionable corner betting intelligence! 🚀 