# Build result

Status: **PASS — actual .NET compilation and official .algo packaging completed**.

- Target: .NET 6; SDK 6.0.428; MSBuild 17.3.4.
- Official platform package: cTrader.Automate **1.0.19**, pinned after NuGet version verification.
- No third-party strategy/runtime packages. The official API/build package is required for external compilation.
- Source namespace: `cAlgo.Robots`; public Robot class: `CumulativeDeltaScalper_EURUSD_v1`.
- `[Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]`.
- Compiled against real cAlgo.API.dll, not a mock/stub. Compiler reported no C# warnings/errors.
- Actual output: `builds/CumulativeDeltaScalper_EURUSD_v1.algo`.
- Import/execution in cTrader UI/Cloud has not yet been verified. Compilation is not a performance or live-trading acceptance test.

## Reproduce

```sh
dotnet build src/CumulativeDeltaScalper_EURUSD_v1.csproj -c Release
```

In this container the dotnet CLI startup encountered a process-information error. Invoking the installed official MSBuild entry point succeeded:

```sh
/tmp/cds-dotnet/dotnet /tmp/cds-dotnet/sdk/6.0.428/MSBuild.dll src/CumulativeDeltaScalper_EURUSD_v1.csproj -restore -t:Rebuild -p:Configuration=Release -v:minimal
```

The pinned package names its intermediate algo from the project parent directory. Copying is performed after `_AlgoBuildAfterBuild`, to the exact requested filename. An initial copy target ran too early; this was corrected before the successful build.

`src/CumulativeDeltaScalper_EURUSD_v1.cs` is standalone: create a cBot of that name in Automate and replace the entire generated source with this file. No additional source files are needed.

## API audit

| API | Checked implementation |
| --- | --- |
| ExecuteMarketOrder | Six-argument overload: direction, symbol, volume units, label, SL pips, TP pips |
| ModifyPosition | Four-argument overload with `ProtectionType.Absolute`; preserves TP |
| History | HistoricalTrade SymbolName, Label, EntryTime, ClosingTime, NetProfit, PositionId; all compile |
| Positions | Count, LINQ enumeration, Closed event, Position Id/EntryTime/SL/TP; all compile |
| Symbol | MinStopLossDistance, MinTakeProfitDistance, MinDistanceType, NormalizeVolumeInUnits, VolumeForFixedRisk, AmountRisked, GetEstimatedMargin; all compile |
| TimeFrame | Explicit cAlgo.API.TimeFrame.Minute/Minute5/Minute15/Minute30 comparisons |
| Indicators | ATR and Bars-based DirectionalMovementSystem overload compile; closed-bar values used |

Official references checked: https://help.ctrader.com/ctrader-algo/documentation/all-algos/compiling/ ; https://help.ctrader.com/ctrader-algo/references/MarketData/Symbols/Symbol/ ; https://help.ctrader.com/ctrader-algo/references/MarketData/Symbols/SymbolMinDistanceType/ ; https://help.ctrader.com/ctrader-algo/references/Indicators/IIndicatorsAccessor/
