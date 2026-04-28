# 登入、個人資料與輪詢

本頁整理 `LINE` 初始化、個人資料與 operation 輪詢相關 API。

## `LINE(...)`

建立 LINE client。相容層內部會建立 CHRLINE-Patch client，並把 `profile` 包成 `AttrProxy`。

```python
from line_api_compat import LINE

cl = LINE("line@example.com", "password")
print(cl.mid)
print(cl.authToken)
```

常用屬性：

| 屬性 | 說明 |
| --- | --- |
| `cl.mid` | Bot 自己的 MID。 |
| `cl.authToken` | 登入後取得的 auth token。 |
| `cl.revision` | LINE operation revision，可讀寫。 |
| `cl.profile` | Bot profile，支援 `profile.mid`、`profile.displayName`。 |

## `getProfile()`

重新取得自己的 profile，並更新 `cl.profile`。

```python
profile = cl.getProfile()
print(profile.displayName)
```

## `updateProfile(profile)`

更新顯示名稱與狀態訊息。傳入物件只要有 `displayName` 或 `statusMessage` 屬性即可。

```python
profile = cl.getProfile()
profile.displayName = "Chino Bot"
profile.statusMessage = "online"
cl.updateProfile(profile)
```

這個方法目前只會更新：

| 屬性 | CHRLINE attribute id |
| --- | --- |
| `displayName` | `2` |
| `statusMessage` | `16` |

## `updateProfileAttribute(attrId, value)`

直接呼叫 CHRLINE-Patch 的 profile attribute 更新。

```python
cl.updateProfileAttribute(2, "New Name")
```

## `fetchOperation(revision, count=100)`

相容舊寫法，實際上會呼叫 `fetchOps(revision, count)`。

```python
ops = cl.fetchOperation(cl.revision, count=50)
```

## `fetchOps(revision, count=100)`

取得 LINE operations。若目前裝置支援 sync，會改用 `sync`；否則使用 `fetchOps`。

```python
for op in cl.fetchOps(cl.revision, 100):
    print(op.type)
```

回傳值會被包成 `Operation` 類型的 `AttrProxy`，可使用：

```python
op.type
op.param1
op.param2
op.param3
op.message
```

## `setRevision(revision)`

設定底層 client revision。

```python
cl.setRevision(op.revision)
```

## `OEPoll`

`OEPoll` 是主程式輪詢用的小包裝。

```python
from line_api_compat import OEPoll

poll = OEPoll(cl)
ops = poll.singleTrace(count=1)
```

### `singleTrace(count=1, fetchOperations=None)`

用目前 `client.revision` 取得 operations。發生 `TimeoutError` 時回傳空清單；其他錯誤會寫入 `client.log()` 後回傳空清單，避免主迴圈直接中斷。

```python
ops = poll.singleTrace(count=10)
for op in ops:
    if getattr(op, "revision", None):
        poll.setRevision(op.revision)
```

如果需要測試或替換取得 operation 的來源，可傳入 `fetchOperations`：

```python
ops = poll.singleTrace(count=10, fetchOperations=my_fetch)
```
