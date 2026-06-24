import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Bell,
  BookOpen,
  Boxes,
  CreditCard,
  Play,
  RefreshCw,
  ShoppingCart,
  UserPlus,
} from "lucide-react";
import "./styles.css";

const API_BASE = "http://localhost:8080";

type ApiResponse<T> = {
  success: boolean;
  message: string;
  data: T;
  errors: { code: string; message: string; field?: string | null }[];
  meta: unknown;
};

type User = {
  id: string;
  email: string;
  full_name: string;
  role: string;
};

type Product = {
  id: string;
  name: string;
  description: string | null;
  price: string;
  stock: number;
  category_id: string | null;
};

type Order = {
  id: string;
  user_id: string;
  status: string;
  total_amount: string;
  payment_id: string | null;
  cancellation_reason: string | null;
};

type NotificationItem = {
  id: string;
  recipient: string;
  type: string;
  message: string;
  status: string;
  created_at: string;
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const body = (await response.json()) as ApiResponse<T>;
  if (!response.ok || !body.success) {
    throw new Error(body.errors?.[0]?.message || body.message || "Request failed");
  }
  return body.data;
}

function App() {
  const suffix = useMemo(() => Math.floor(Date.now() / 1000), []);
  const [email, setEmail] = useState(`demo${suffix}@example.com`);
  const [password, setPassword] = useState("password123");
  const [fullName, setFullName] = useState("Demo User");
  const [productName, setProductName] = useState(`Microservice Book ${suffix}`);
  const [price, setPrice] = useState("29.99");
  const [stock, setStock] = useState("10");
  const [quantity, setQuantity] = useState("1");
  const [forcePaymentFail, setForcePaymentFail] = useState(false);

  const [user, setUser] = useState<User | null>(null);
  const [selectedProductId, setSelectedProductId] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [log, setLog] = useState("Ready.");
  const [busy, setBusy] = useState(false);

  const appendLog = (message: string) => {
    setLog((current) => `${new Date().toLocaleTimeString()}  ${message}\n${current}`);
  };

  const run = async (label: string, action: () => Promise<void>) => {
    setBusy(true);
    try {
      appendLog(`Starting: ${label}`);
      await action();
      appendLog(`Done: ${label}`);
    } catch (error) {
      appendLog(`Error: ${(error as Error).message}`);
    } finally {
      setBusy(false);
    }
  };

  const refreshProducts = async () => {
    const data = await request<Product[]>("/api/v1/products");
    setProducts(data);
    if (!selectedProductId && data[0]) setSelectedProductId(data[0].id);
  };

  const refreshNotifications = async () => {
    const data = await request<NotificationItem[]>("/api/v1/notifications");
    setNotifications(data);
  };

  const register = () =>
    run("Register user", async () => {
      const data = await request<User>("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, full_name: fullName }),
      });
      setUser(data);
      appendLog(`User: ${data.id}`);
    });

  const createProduct = () =>
    run("Create product", async () => {
      const data = await request<Product>("/api/v1/products", {
        method: "POST",
        body: JSON.stringify({
          name: productName,
          description: "Created from React console",
          price,
          stock: Number(stock),
        }),
      });
      setSelectedProductId(data.id);
      await refreshProducts();
      appendLog(`Product: ${data.id}`);
    });

  const createOrder = () =>
    run("Create order", async () => {
      if (!user) throw new Error("Register a user first.");
      if (!selectedProductId) throw new Error("Create or select a product first.");

      const data = await request<Order>("/api/v1/orders", {
        method: "POST",
        body: JSON.stringify({
          user_id: user.id,
          force_payment_fail: forcePaymentFail,
          items: [{ product_id: selectedProductId, quantity: Number(quantity) }],
        }),
      });

      setOrders((current) => [data, ...current]);
      await refreshProducts();
      await refreshNotifications();
      appendLog(`Order ${data.id}: ${data.status}`);
    });

  const runHappyPath = () =>
    run("Happy path", async () => {
      const createdUser = await request<User>("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email: `happy${Date.now()}@example.com`,
          password: "password123",
          full_name: "Happy Path User",
        }),
      });
      setUser(createdUser);

      const product = await request<Product>("/api/v1/products", {
        method: "POST",
        body: JSON.stringify({
          name: `Happy Path Product ${Date.now()}`,
          description: "One-click flow product",
          price: "19.99",
          stock: 5,
        }),
      });
      setSelectedProductId(product.id);

      const order = await request<Order>("/api/v1/orders", {
        method: "POST",
        body: JSON.stringify({
          user_id: createdUser.id,
          items: [{ product_id: product.id, quantity: 1 }],
        }),
      });

      setOrders((current) => [order, ...current]);
      await refreshProducts();
      await refreshNotifications();
      appendLog(`Happy path order ${order.status}`);
    });

  return (
    <main className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">MS</span>
          <span>Ecommerce Microservices Console</span>
        </div>
        <nav className="links" aria-label="Swagger links">
          <a href="http://localhost:8001/docs" target="_blank">User docs</a>
          <a href="http://localhost:8002/docs" target="_blank">Product docs</a>
          <a href="http://localhost:8003/docs" target="_blank">Order docs</a>
          <a href="http://localhost:8004/docs" target="_blank">Payment docs</a>
          <a href="http://localhost:8005/docs" target="_blank">Notification docs</a>
        </nav>
      </header>

      <section className="layout">
        <aside className="sidebar">
          <button disabled={busy} onClick={runHappyPath}>
            <Play size={16} /> Run happy path
          </button>
          <button className="secondary" disabled={busy} onClick={() => run("Refresh data", async () => {
            await refreshProducts();
            await refreshNotifications();
          })}>
            <RefreshCw size={16} /> Refresh data
          </button>
          <div className="panel">
            <h3>Current Context</h3>
            <div className="stack muted">
              <div>User: {user?.id ?? "none"}</div>
              <div>Product: {selectedProductId || "none"}</div>
              <div>Gateway: {API_BASE}</div>
            </div>
          </div>
          <div className="panel">
            <h3>Runtime Log</h3>
            <div className="log">{log}</div>
          </div>
        </aside>

        <section className="workspace">
          <div className="grid">
            <section className="panel">
              <h2><UserPlus size={17} /> User Service</h2>
              <div className="form">
                <label>Email<input value={email} onChange={(event) => setEmail(event.target.value)} /></label>
                <label>Password<input value={password} onChange={(event) => setPassword(event.target.value)} /></label>
                <label>Full name<input value={fullName} onChange={(event) => setFullName(event.target.value)} /></label>
                <button disabled={busy} onClick={register}><UserPlus size={16} /> Register</button>
              </div>
            </section>

            <section className="panel">
              <h2><Boxes size={17} /> Product Service</h2>
              <div className="form">
                <label>Name<input value={productName} onChange={(event) => setProductName(event.target.value)} /></label>
                <div className="row">
                  <label>Price<input value={price} onChange={(event) => setPrice(event.target.value)} /></label>
                  <label>Stock<input value={stock} onChange={(event) => setStock(event.target.value)} /></label>
                </div>
                <button disabled={busy} onClick={createProduct}><Boxes size={16} /> Create product</button>
              </div>
            </section>
          </div>

          <div className="grid">
            <section className="panel">
              <h2><ShoppingCart size={17} /> Order Service</h2>
              <div className="form">
                <label>Product
                  <select value={selectedProductId} onChange={(event) => setSelectedProductId(event.target.value)}>
                    <option value="">Select product</option>
                    {products.map((product) => (
                      <option key={product.id} value={product.id}>
                        {product.name} - stock {product.stock}
                      </option>
                    ))}
                  </select>
                </label>
                <label>Quantity<input value={quantity} onChange={(event) => setQuantity(event.target.value)} /></label>
                <label className="row">
                  <input
                    type="checkbox"
                    checked={forcePaymentFail}
                    onChange={(event) => setForcePaymentFail(event.target.checked)}
                  />
                  Force payment failure
                </label>
                <button disabled={busy} onClick={createOrder}><CreditCard size={16} /> Create order</button>
              </div>
            </section>

            <section className="panel">
              <h2><BookOpen size={17} /> Latest Orders</h2>
              <div className="list">
                {orders.length === 0 && <div className="muted">No orders yet.</div>}
                {orders.map((order) => (
                  <div className="item" key={order.id}>
                    <strong>{order.id}</strong>
                    <span className="pill">{order.status}</span>
                    <span className="muted">Total: {order.total_amount}</span>
                    {order.cancellation_reason && <span className="muted">{order.cancellation_reason}</span>}
                  </div>
                ))}
              </div>
            </section>
          </div>

          <div className="grid">
            <section className="panel">
              <h2><Boxes size={17} /> Products</h2>
              <div className="list">
                {products.length === 0 && <div className="muted">Create a product or refresh data.</div>}
                {products.map((product) => (
                  <button className="item secondary" key={product.id} onClick={() => setSelectedProductId(product.id)}>
                    <strong>{product.name}</strong>
                    <span className="muted">{product.price} - stock {product.stock}</span>
                  </button>
                ))}
              </div>
            </section>

            <section className="panel">
              <h2><Bell size={17} /> Notifications</h2>
              <div className="list">
                {notifications.length === 0 && <div className="muted">No notifications yet.</div>}
                {notifications.map((item) => (
                  <div className="item" key={item.id}>
                    <strong>{item.type}</strong>
                    <span>{item.message}</span>
                    <span className="muted">{item.status}</span>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </section>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
