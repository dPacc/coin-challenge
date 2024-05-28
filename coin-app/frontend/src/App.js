import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link,
  useLocation,
} from "react-router-dom";
import { Layout, Menu } from "antd";
import { GithubOutlined } from "@ant-design/icons";
import UploadImage from "./components/UploadImage";
import ImageList from "./components/ImageList";
import "./App.css";

const { Header, Content, Footer } = Layout;

const NavigationHeader = () => {
  const location = useLocation();

  const getCurrentMenuKey = () => {
    switch (location.pathname) {
      case "/images":
        return "2";
      case "/":
      default:
        return "1";
    }
  };

  return (
    <Header className="layout-header">
      <Link to="/">
        <div className="logo">
          <img
            src="https://aiqintelligence.ae/application/themes/aiqtheme/assets/images/logo.svg"
            alt="AIQ Logo"
          />
        </div>
      </Link>
      <Menu
        theme="dark"
        mode="horizontal"
        defaultSelectedKeys={[getCurrentMenuKey()]}
        className="menu"
      >
        <Menu.Item key="1">
          <Link to="/">Upload Image</Link>
        </Menu.Item>
        <Menu.Item key="2">
          <Link to="/images">Image List</Link>
        </Menu.Item>
      </Menu>
      <div className="github-icon">
        <a
          href="https://github.com/dPacc/coin-challenge"
          target="_blank"
          rel="noopener noreferrer"
        >
          <GithubOutlined
            style={{
              fontSize: "22px",
              color: "black",
              marginTop: "24px",
              marginLeft: "16px",
            }}
          />
        </a>
      </div>
    </Header>
  );
};

const App = () => {
  return (
    <Router>
      <Layout className="layout">
        <NavigationHeader />
        <Content style={{ padding: "0 50px", overflow: "auto" }}>
          <div className="site-layout-content">
            <Routes>
              <Route path="/" element={<UploadImage />} />
              <Route path="/images" element={<ImageList />} />
            </Routes>
          </div>
        </Content>
        <Footer style={{ textAlign: "center" }} className="footer">
          AIQ ©2024 ~ Made by{" "}
          <a
            href="https://github.com/dPacc/coin-challenge"
            target="_blank"
            rel="noopener noreferrer"
          >
            dPacc
          </a>
        </Footer>
      </Layout>
    </Router>
  );
};

export default App;
