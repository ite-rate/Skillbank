# 思路码样本(Go 版)

翻译前对照样本定粒度。这些样本是用户反复校准出来的,不是翻译器自己挑的。

---

## 样本 1:LeetCode 94 中序遍历(用户亲手校准的粒度)

这是用户给的标准。粒度:**方法调用全中文化,动作用中文动词,`for`/`if` 保留关键字**。

### 源码(Go)

```go
func inorderTraversal(root *TreeNode) []int {
    stack := []*TreeNode{}
    res := []int{}
    curr := root
    for curr != nil || len(stack) > 0 {
        for curr != nil {
            stack = append(stack, curr)
            curr = curr.Left
        }
        curr = stack[len(stack)-1]
        stack = stack[:len(stack)-1]
        res = append(res, curr.Val)
        curr = curr.Right
    }
    return res
}
```

### 思路码

```
inorderTraversal(root):
  定义栈 定义结果
  root给cur
  for cur不空 或 栈不空:
    for cur不空:
      cur压栈; cur走左
    cur空,弹出栈顶给cur
    cur的值追加到res
    cur走右
  返回res
```

### 关键校准点
- `stack = append(stack, curr)` → `cur压栈`(方法调用去掉,中文动词)
- `curr = curr.Left` → `cur走左`(赋值用"走",不是"赋值为 curr.Left")
- `curr != nil || len(stack) > 0` → `cur不空 或 栈不空`(`||` 换"或",`!= nil` 换"不空",`len(stack)>0` 换"栈不空")
- `res = append(res, curr.Val)` → `cur的值追加到res`
- `for`/`return` 保留关键字

---

## 样本 2:Go HTTP server(用户校准的"激进版")

用户在多版本中选了这版。粒度:**短函数压一行,意图嵌在动作尾部,字段声明带类型**。

### 源码(Go)

```go
type Server struct {
    mu     sync.Mutex
    counts map[string]int
    srv    *http.Server
}

func NewServer(addr string) *Server {
    s := &Server{counts: make(map[string]int)}
    mux := http.NewServeMux()
    mux.HandleFunc("/incr", s.handleIncr)
    mux.HandleFunc("/count", s.handleCount)
    s.srv = &http.Server{Addr: addr, Handler: mux}
    return s
}

func (s *Server) handleIncr(w http.ResponseWriter, r *http.Request) {
    key := r.URL.Query().Get("key")
    if key == "" {
        http.Error(w, "missing key", 400)
        return
    }
    s.mu.Lock()
    s.counts[key]++
    s.mu.Unlock()
    fmt.Fprintf(w, "ok\n")
}

func (s *Server) handleCount(w http.ResponseWriter, r *http.Request) {
    key := r.URL.Query().Get("key")
    s.mu.Lock()
    n := s.counts[key]
    s.mu.Unlock()
    json.NewEncoder(w).Encode(map[string]int{key: n})
}

func (s *Server) Start() {
    go s.srv.ListenAndServe()
}

func (s *Server) Stop(ctx context.Context) error {
    return s.srv.Shutdown(ctx)
}

func main() {
    s := NewServer(":8080")
    s.Start()
    fmt.Println("listening on :8080")
    time.Sleep(10 * time.Second)
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()
    if err := s.Stop(ctx); err != nil {
        fmt.Println("shutdown error:", err)
    }
    fmt.Println("bye")
}
```

### 思路码

```
Go 结构体 Server:
  字段 mu       (sync.Mutex)        保护 counts
  字段 counts   (map[string]int)    共享计数表
  字段 srv      (*http.Server)      底层 server

NewServer(addr):  建空表, 注册路由 /incr→handleIncr /count→handleCount, srv绑addr, 返回

handleIncr(w, r):  拿 key 参数, 空则 400 return, 加锁count加加, 写 "ok"
handleCount(w, r): 拿 key 参数, 加锁读count存n, JSON 编码 {key:n} 写回

Start:  go srv.ListenAndServe()    后台起 错误被吞
Stop(ctx):  return srv.Shutdown(ctx)   优雅关闭带超时

main:
  新server启动在8080
  Start
  睡10s
  定义待超时5s的取消 defer取消
  s.Stop(ctx) err不空打印
  打印 "bye"
```

### 关键校准点
- 字段声明保留类型(`(sync.Mutex)`),类型决定行为,Go 程序员看类型就知道语义
- 短函数压成一行:`Start: go srv.ListenAndServe()    后台起 错误被吞`(动作 + 意图注释)
- `s.mu.Lock(); s.counts[key]++; s.mu.Unlock` → `加锁count加加`(三步压成一个动作短语)
- `ctx, cancel := context.WithTimeout(...)` → `定义待超时5s的取消`(意图嵌进动作)
- `if err != nil { fmt.Println(...) }` → `s.Stop(ctx) err不空打印`(条件+动作压一行)
- 关键数字保留("8080""10s""5s")——是脑补源码的锚点

---

## 样本 3:LeetCode 160 相交链表(用户纠正的"反例")

用户指出这版用了 `?:` 三目运算,要翻译。这是**反面教材**,记录避免再犯。

### 错误版(被用户拒绝)

```
getIntersectionNode(headA, headB):
  pA = headA, pB = headB
  for pA != pB:
    pA = (pA == nil) ? headB : pA.Next    A 走完接 B 的头
    pB = (pB == nil) ? headA : pB.Next    B 走完接 A 的头
  return pA
```

**问题**:`?:` 是 C 系语法噪音,读者要在脑子里解析三目运算。

### 正确版

```
getIntersectionNode(headA, headB):
  pA = headA, pB = headB
  for pA != pB:
    pA 到尾了就跳到 headB, 否则走下一步
    pB 到尾了就跳到 headA, 否则走下一步
  return pA
```

### 关键校准点
- `?:` → "到尾了就..., 否则..."(条件动作用中文表达)
- 动作整句用中文,不调用函数语法
- `return pA` 保留(Go 关键字)

---

## 样本 4:LeetCode 138 复制带随机指针的链表(连续点访问拆开)

用户指出 `p.Next.Next`、`p.Random.Next` 这种连续点访问要拆开,加中间变量。

### 错误片段(被用户纠正)

```
for p = head; p != nil; p = p.Next.Next:
  if p.Random != nil: p.Next.Random = p.Random.Next
```

**问题**:连续点访问,读者要在脑子里拆 `p.Next` 是什么、`p.Random.Next` 又是什么。

### 正确版

```
# 第二遍:给副本设 Random
p = head
for p != nil:
  copy = p.Next                   p 的副本(就在 p 后面)
  if p.Random != nil:
    copy.Random = p.Random.Next   原 Random 的副本
  p = copy.Next                   跳到下一个原节点
```

### 关键校准点
- `p.Next.Next` 拆开:先 `copy = p.Next`,再用 `copy.Next`
- 中间变量加意图注释(`copy = p.Next   p 的副本(就在 p 后面)`)
- 嵌套访问拆成单层访问 + 变量

---

## 样本 5:mini_ros2 pub_sub(多模块粒度,非算法题)

用户最初设想的场景:读 ROS2 源码时省语法带宽。粒度:**模块分块 + 责任一句话 + 入口一行意图 + 约束一句话 + 漏掉的处理**。

### 思路码

```
Pub/Sub:
  跨进程跨机器的单向消息广播;每个 Publisher 持一个 ZMQ PUB socket,每个 Subscriber 持一个 SUB socket + 后台线程
  Publisher<T>.publish(msg): 序列化 msg,送进 socket 缓冲,立即返回
  Subscriber<T>.on_message(cb): 连接对端,起后台线程循环收,每条消息反序列化后调 cb
  并发约束:cb 跑在后台线程,用户在 cb 里访问的任何外部状态都要自己加锁;context_t 必须比所有 socket 长命

Node:
  持有 zmq context + Discovery,对外暴露 advertise/subscribe 工厂方法
  advertise<T>(topic, port) → Publisher<T>:把 (topic,port) 登记进 Discovery,创建 PUB socket 绑定 port
  subscribe<T>(host, port, cb) → Subscriber<T>:创建 SUB socket 连接 host:port,起后台线程

使用方(仿照 ROS2 talker/listener):
  talker: advertise("chatter", 5555),每 1s publish 一条 StringMsg
  listener: subscribe(talker_host, 5555, cb),cb 里打印消息

漏掉的处理:
  - PUB/SUB 默认 best_effort,订阅者慢或重连期间的消息会丢,没有可靠性保证
  - publish 不报错:即使没订阅者、对端挂了,也静默成功
  - Subscriber 析构时后台线程靠 stop 标志退出,但 recv 阻塞时 stop 检查有延迟
  - 同名 topic 多个 Publisher,Subscriber 只连了一个 host:port(没做多端订阅)
  - 没有反压:发布过快,订阅者收不过来,ZMQ 会丢或内存涨
```

### 关键校准点
- 不写源码(`template<typename T> class Publisher`),写入口签名 + 一句意图
- "并发约束"独立一行,不混进接口
- "漏掉的处理"列**源码里没做但影响行为的点**(不是设计决策,是缺什么)
- 跨模块关系用独立小块表达(Node 持有 Pub/Sub 的 context,使用方调 advertise/subscribe)

---

## 粒度冲突时的优先级

如果样本之间粒度不一致(比如样本 1 的算法题粒度 vs 样本 5 的模块粒度),按**用户当前任务类型**选:

- 任务是**算法题** → 用样本 1/3/4 的粒度
- 任务是**读 Go 项目源码** → 用样本 2 的粒度
- 任务是**多模块系统设计** → 用样本 5 的粒度

用户给新样本时,**新样本覆盖同类型的旧样本**。