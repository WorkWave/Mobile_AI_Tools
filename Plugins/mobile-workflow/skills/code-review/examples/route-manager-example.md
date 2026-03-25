# Example: RouteManager.GetRouteListAsync

**Source:** `RG.Mobile.Core/Managers/Route/RouteManager.cs` (lines 281–344)
**Codebase:** RealGreen Mobile (RG)

## Code

```csharp
public async Task<List<RouteObj>> GetRouteListAsync(Employee employee, bool hasMarketLevelSecurity, bool hasRegionLevelSecurity, bool hasCorporateLevelSecurity)
{
    List<RouteObj> routesList = new List<RouteObj>();
    var route = (await DbProxy.AllWithChildrenAsync<RouteObj>()).FirstOrDefault();
    string sql = "SELECT [Route] Route, Route_Desc, [RouteObj].[Emp_ID] Emp_ID FROM [RouteObj] WHERE Route_Desc IS NOT NULL AND [Available] = 1 AND Comp_ID = @Comp_ID ";
    sql = employee.Comp_ID.HasValue ? sql.Replace("@Comp_ID", employee.Comp_ID.Value.ToString()) : sql.Replace("AND Comp_ID = @Comp_ID ", " ");

    if (hasMarketLevelSecurity || hasRegionLevelSecurity || hasCorporateLevelSecurity)
    {
        StringBuilder mrcSql = new StringBuilder();
        mrcSql.Append("SELECT _id Route, Route_Desc, emp Emp_ID FROM ( ");
        mrcSql.Append("SELECT [Route] _id, Route_Desc, [RouteObj].[Emp_ID] emp  ");
        mrcSql.Append("FROM ");
        if (hasCorporateLevelSecurity)
        {
            mrcSql.Append("[RouteObj]");
        }
        else if (hasRegionLevelSecurity)
        {
            mrcSql.Append("Employee AS MyEmployee ");
            mrcSql.Append("JOIN CompanyObj AS MyCompany ON MyEmployee.Comp_ID = MyCompany.Comp_ID ");
            mrcSql.Append("JOIN MarketObj AS MyMarket ON MyCompany.MarketID = MyMarket.MarketID ");
            mrcSql.Append("JOIN RegionObj AS MyRegion ON MyMarket.RegionID = MyRegion.RegionID ");
            mrcSql.Append("JOIN MarketObj AS RegionMarkets ON MyRegion.RegionID = RegionMarkets.RegionID ");
            mrcSql.Append("JOIN CompanyObj AS RegionCompanies ON RegionMarkets.MarketID = RegionCompanies.MarketID ");
            mrcSql.Append("JOIN RouteObj ON RegionCompanies.Comp_ID = [RouteObj].Comp_ID ");
        }
        else if (hasMarketLevelSecurity)
        {
            mrcSql.Append("Employee AS MyEmployee ");
            mrcSql.Append("JOIN CompanyObj AS MyCompany ON MyEmployee.Comp_ID = MyCompany.Comp_ID ");
            mrcSql.Append("JOIN CompanyObj AS MarketCompany ON MyCompany.MarketID = MarketCompany.MarketID ");
            mrcSql.Append("JOIN RouteObj ON MarketCompany.Comp_ID = [RouteObj].Comp_ID ");
        }

        mrcSql.Append("WHERE Route_Desc IS NOT NULL AND [Available] = 1 ");

        if (!hasCorporateLevelSecurity)
        {
            mrcSql.Append("AND MyEmployee.Emp_ID = '" + employee.Emp_ID.Replace("'", "''") + "' ");
        }

        mrcSql.Append(" UNION ");
        mrcSql.Append(sql);

        if (!string.IsNullOrWhiteSpace(route.Route)) // getting the customers branch, if it's not returned in the MRC results
        {
            mrcSql.Append(" UNION SELECT [Route] _id, Route_Desc, [RouteObj].[Emp_ID] emp FROM [RouteObj] WHERE Route_Desc IS NOT NULL AND [Available] = 1 AND [Route] = '" + route.Route.Trim() + "'");
        }

        mrcSql.Append(") GROUP BY _id, Route_Desc, emp ");
        sql = mrcSql.ToString();
    }

    sql = "SELECT '' AS Route, 'None' AS Route_Desc, '' AS Emp_ID UNION " + sql.ToString();

    Console.WriteLine(sql.ToString());

    routesList = (await DatabaseProxy.QueryAsync<RouteObj>(sql.ToString())).ToList();

    routesList = routesList.Where(r => !string.IsNullOrWhiteSpace(r.Route)).ToList();

    return routesList;
}
```

## Expected Review Output

**Summary:** Needs changes — SQL injection vulnerabilities and a null dereference risk require fixes before merge.

**Changes Made:** Single method in `RouteManager.cs` building dynamic SQL for route list queries with multi-level security filtering.

**Findings:**

| Severity | Category | Finding | Recommendation |
|----------|----------|---------|----------------|
| Critical | Security | Line 320: `employee.Emp_ID` concatenated directly into SQL. Manual `'` → `''` escaping is not sufficient protection against SQL injection. | Use parameterized queries via `DatabaseProxy` |
| Critical | Security | Line 328: `route.Route.Trim()` also directly concatenated into SQL with no escaping at all. | Use parameterized queries |
| Major | Null Reference | Line 284: `FirstOrDefault()` can return `null`. Line 326 dereferences `route.Route` without first checking `route != null`. | Add `if (route == null) return routesList;` after line 284 |
| Major | Debug Code | Line 337: `Console.WriteLine(sql)` left in production code. | Remove |
| Minor | Performance | Line 341: `!string.IsNullOrWhiteSpace(r.Route)` filter runs in C# after the full result set is fetched. | Push filter into SQL `WHERE` clause |
| Advisory | SRP | Method handles three distinct security-level query shapes plus a fallback — it has grown too large for a single method. | Extract private helpers per security level |

**What's Good:**
- Async/await used correctly throughout — no `.Result` or `.Wait()` calls
- Correctly delegates data access to `DbProxy` / `DatabaseProxy` rather than accessing storage directly
- Boolean parameter names (`hasMarketLevelSecurity`, etc.) are clear and self-documenting

**Next Steps:**
1. Replace string-concatenated SQL with parameterized queries (Critical)
2. Add null guard on `route` after `FirstOrDefault()` (Major)
3. Remove `Console.WriteLine` (Major)
4. Move `IsNullOrWhiteSpace` filter into SQL WHERE clause (Minor)
5. Consider refactoring security-level branches into private helpers (Advisory)
