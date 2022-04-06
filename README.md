##### Poster

海报生成

[原项目地址](https://github.com/psoho/fast-poster)

把原项目的部分代码砍掉，留下需要的部分，将数据库换成了mysql


```bash
# 激活虚拟环境
poetry shell

# 安装依赖
poetry install

cd poster_app/

# 初始化数据表
python init_db.py

# 启动项目
python fast.py
```


---
that's all
