#!/usr/bin/env python3

print("🎯 FAVORITE vs UNDERDOG PSYCHOLOGY - CORNER BETTING REVOLUTION")
print("=" * 80)
print()

print("💡 KEY INSIGHT: WHO is trailing matters more than WHAT the score is!")
print()

print("🔥 EXTREME URGENCY SCENARIOS (22.5+ points):")
print("   📊 HEAVY FAVORITE trailing 0-1, 1-2 at 75+ minutes")
print("   💰 Odds examples: Man City 1.25 vs Burnley 8.00, City trailing")
print("   🎯 Result: CORNER GOLDMINE - Quality players desperately attacking")
print()

print("⚡ VERY HIGH URGENCY SCENARIOS (19.5+ points):")
print("   📊 STRONG FAVORITE trailing 0-1, 1-2 at 70+ minutes")
print("   💰 Odds examples: Arsenal 1.50 vs Brighton 6.00, Arsenal trailing")
print("   🎯 Result: EXCELLENT corner potential - Sustained quality pressure")
print()

print("🟢 HIGH URGENCY SCENARIOS (15-16.5 points):")
print("   📊 MODERATE FAVORITE trailing 0-1 at 70+ minutes")
print("   📊 UNDERDOG leading vs HEAVY FAVORITE at 70+ minutes")
print("   💰 Odds examples: Liverpool 1.80 vs West Ham 4.50")
print("   🎯 Result: GOOD corner potential - Pressure with quality")
print()

print("🟡 MEDIUM URGENCY SCENARIOS (8-12 points):")
print("   📊 FAVORITE leading 1-0 (underdog attacking but limited quality)")
print("   📊 Two goal difference regardless of odds")
print("   🎯 Result: PROCEED WITH CAUTION - Limited attacking quality")
print()

print("🔴 LOW URGENCY SCENARIOS (0-5 points):")
print("   📊 3+ goal difference - Game decided")
print("   🎯 Result: AVOID - No motivation regardless of quality")
print()

print("📊 PRACTICAL EXAMPLES:")
print("-" * 50)

scenarios = [
    {
        'match': "Man City (1.20) vs Sheffield United (12.00)",
        'score': "0-1 at 78 minutes",
        'analysis': "HEAVY FAVORITE trailing",
        'psychology_score': 40.5,  # 22.5 * 1.8 late game
        'recommendation': "🔥 EXTREME BUY",
        'reasoning': "Elite players desperately attacking weak defense"
    },
    {
        'match': "Arsenal (1.60) vs Crystal Palace (5.50)",
        'score': "1-2 at 82 minutes", 
        'analysis': "STRONG FAVORITE trailing",
        'psychology_score': 29.3,  # 19.5 * 1.5 late game
        'recommendation': "⚡ STRONG BUY",
        'reasoning': "Quality attacking players in desperation mode"
    },
    {
        'match': "Burnley (6.00) vs Liverpool (1.45)",
        'score': "1-0 at 75 minutes",
        'analysis': "UNDERDOG leading vs STRONG FAVORITE", 
        'psychology_score': 21.6,  # 14.4 * 1.5 late game
        'recommendation': "🟢 BUY",
        'reasoning': "Liverpool will throw everything forward"
    },
    {
        'match': "Brighton (2.20) vs Norwich (3.40)",
        'score': "1-1 at 85 minutes",
        'analysis': "Even teams, draw",
        'psychology_score': 18.0,  # 12 * 1.5 late game
        'recommendation': "🟡 BUY",
        'reasoning': "Both teams pushing for winner"
    },
    {
        'match': "Chelsea (1.30) vs Watford (8.00)",
        'score': "2-0 at 77 minutes",
        'analysis': "HEAVY FAVORITE leading comfortably",
        'psychology_score': 8.0,
        'recommendation': "🔴 AVOID",
        'reasoning': "No urgency, may coast to victory"
    }
]

for scenario in scenarios:
    print(f"\n🏆 {scenario['match']}")
    print(f"   Score: {scenario['score']} | {scenario['analysis']}")
    print(f"   Psychology Score: {scenario['psychology_score']:.1f}")
    print(f"   → {scenario['recommendation']}: {scenario['reasoning']}")

print("\n" + "=" * 80)
print("🧠 PSYCHOLOGY SCORING BREAKDOWN:")
print()

print("📊 BASE SCORES (before late game multipliers):")
print("   🔥 Heavy Favorite Trailing:    22.5 points")
print("   ⚡ Strong Favorite Trailing:   19.5 points") 
print("   🟢 Moderate Favorite Trailing: 16.5 points")
print("   🟡 Underdog Leading vs Heavy:  16.8 points")
print("   🟡 Underdog Leading vs Strong: 14.4 points")
print("   🟠 Any Draw (1-1, 2-2):        12.0 points")
print("   🟠 0-0 Draw:                   8.0 points")
print("   ⚠️ Favorite Leading:           8.0 points")
print("   🔴 Two Goal Difference:        5.0 points")
print("   🔴 Three+ Goal Difference:     0.0 points")
print()

print("⏰ LATE GAME MULTIPLIERS (70+ minutes):")
print("   🔥 Extreme Urgency: ×1.8")
print("   ⚡ Very High Urgency: ×1.5") 
print("   🟢 High Urgency: ×1.3")
print("   🟡 Medium/Low: ×1.0")
print()

print("🎯 FINAL RECOMMENDATIONS:")
print("   Score ≥25 + Good Stats = 🔥 STRONG BUY")
print("   Score ≥18 + Good Stats = ⚡ BUY")
print("   Score ≥12 + Good Stats = 🟡 WEAK BUY")
print("   Score <12 OR Bad Stats = 🔴 AVOID")
print()

print("💡 REVOLUTIONARY INSIGHT:")
print("   Traditional systems only look at scoreline")
print("   Our system considers WHO is trailing + their attacking quality")
print("   Heavy favorite trailing = Corner betting GOLDMINE! 🏆")
print()

print("🚀 SYSTEM COMPLETE - READY FOR PROFIT! 💰") 