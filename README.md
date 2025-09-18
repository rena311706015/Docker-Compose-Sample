這是一個 Docker Compose 的範例，可以藉由 Kompose 工具將此 Repo 改為 K8s 適用的文件

<img width="295" height="205" alt="image (20)" src="https://github.com/user-attachments/assets/77247de7-cd00-4e90-982e-fe351faf14e7" />
<img width="224" height="171" alt="image (17)" src="https://github.com/user-attachments/assets/bcb6d500-c1e1-4482-ad86-d9f8fe01693a" />

## Tools

1. 下載 **minikube** 做本地開發測試
    
     https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fbinary+download
    
    - `curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64`
    - `sudo install minikube-linux-amd64 /usr/local/bin/minikube && rm minikube-linux-amd64`
2. 下載 **kubectl** 以針對 Kubernetes clusters 執行指令 (Kubernetes 的 CLI
    
     https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/
    
    - `curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"`
    - `sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl`
    - `kubectl version --client`
3. 下載官方提供的 **Kompose** 以根據 docker-compose.yml 快速生成 kubectl 可執行的 yaml 
    
    https://kubernetes.io/zh-cn/docs/tasks/configure-pod-container/translate-compose-kubernetes/
    
    - `curl -L https://github.com/kubernetes/kompose/releases/download/v1.34.0/kompose-linux-amd64 -o kompose`
    - `chmod +x kompose`
    - `sudo mv ./kompose /usr/local/bin/kompose`


## Get Start
1. 啟動 minikube
    
    `minikube start`
    
2. 從本機的 docker 切換到 minikube 的 docker
    
    `eval $(minikube docker-env)` 
    
    `docker info | grep "Name:"`  要顯示為 minikube，不然 minikube 會找不到 docker build image
    
3. build backend 和 frontend 的 image 供 minikube 使用
   
   `docker build -t backend ./backend`  
   `docker build -t frontend ./frontend`
    
4. **產生 kubectl 可用的 yaml**
    
    **進入有 docker-compose.yml 的路徑下執行 `kompose convert`**
    
    **輸出類似 INFO Kubernetes file backend-deployment.yaml created**
    
5. 依據開發需求修改自動生成的 yaml
   
    1. frontend-deployment.yaml 和 backend-deployment.yaml 加上 **imagePullPolicy: IfNotPresent**
        
        這邊預設是 Always，也就是 Kubernetes 會從 Docker Hub 或其他公開/私有容器 registry（像 GCR, ECR, Harbor）pull image，但因為我們沒有要把 image 放到這些平台，所以會反覆遇到 `ImagePullBackOff` 
        
        解決方法就是改成 IfNotPresent，如果本地的 Docker 裡沒有這個 image 才去 pull
        
        ```yaml
        spec:
          containers:
            - image: frontend
              name: frontend
              imagePullPolicy: IfNotPresent
        ```
        
    2. 把 frontend-service.yaml 和 backend-service.yaml 從預設的 ClusterIP 類型轉為方便測試的 NodePort
        
        ```yaml
        spec:
          type: NodePort
          ports:
            - name: "8080"
              port: 8080
              targetPort: 80
        ```
        
6. apply 所有生成的 yaml
    
    `kubectl apply -f .`
    
    輸出類似 service/db created
    
7. 檢查 pods 的狀態
    
    `kubectl get pods`
    
    預期應該全部都要是 Running，也可以加上 `-w` 持續監控所有 pods 的狀態

    <img width="707" height="133" alt="image (18)" src="https://github.com/user-attachments/assets/ce42891d-32fe-48b2-abfb-7d410340c3ff" />
    
8. 檢查 service 的狀態
    
    `kubectl get svc`
   
    <img width="706" height="155" alt="image (19)" src="https://github.com/user-attachments/assets/05bb10ca-54e0-4e80-bb89-b8d74b3eaa03" />
    
9. 這邊因為我們原本 index.html 裡打 API 是 http://localhost:8000/submit ，但在 Kubernetes 中，服務會透過自己的 Cluster IP、NodePort 或 LoadBalancer 曝露給外部，而不使用 localhost
    
    所以我們先取得當前後端服務的 url
    
    `minikube service backend --url` 
    
    再把 index.html 裡的 http://localhost:8000/ 替換成取得的 url
    
    重新載入修正後的 frontend
    
    `docker build --no-cache -t frontend ./frontend`
    
    `kubectl rollout restart deployment frontend`
    
    <aside>
    💡 生產環境下會使用 Ingress 管理叢集內服務 (Service) 對外的 HTTP/HTTPS 存取，就不用 NodePort 和這些步驟，下面會再說要怎麼做
    </aside>
    
10. 測試服務
    
    `minikube service frontend --url`  點擊開啟網頁服務
    
11. 檢查資料庫

    1. `kubectl exec -it <db-pod-name> -- bash` 
    2. `mysql -uroot -prootpass myapp` 
    3. `SELECT * FROM messages;`
      
12. 離開 minikube

    1. `minikube stop`
    2. `minikube delete`
   
## 接著，加上幾個 K8s 才有的功能

### Ingress
   用來管理叢集內服務 (Service) 對外的 HTTP/HTTPS 存取
   
   1. minikube 預設是沒有啟用 Ingress 的，需要手動啟用，啟用後會統一開 http 80 和 https 443 port

      `minikube addons enable ingress`
      
   2. 取得 minikube 在內網的位址

      `minikube ip` 複製印出的 ip 位置
      
   3. `sudo nano /etc/hosts` 後在最底下新增 `<ip> <網域名稱>`  🌰 `192.168.58.2 app.test`  

      這樣在瀏覽器輸入網域名稱後，系統會去 /etc/hosts 查，發現它對應到的 ip 位置，然後就把流量送到 Minikube 容器裡
      
   4. 新增 ingress.yaml

      ```yaml
        apiVersion: networking.k8s.io/v1
        kind: Ingress
        metadata:
          name: ingress
        spec:
          rules:
          - host: app.test
            http:
              paths:
              - path: /submit
                pathType: Prefix
                backend:
                  service:
                    name: backend
                    port:
                      number: 8000
              - path: /
                pathType: Prefix
                backend:
                  service:
                    name: frontend
                    port:
                      number: 8080
        ```

      然後 `kubectl apply -f ingress.yaml`  
      
      這樣 minikube 就可以統一網域名稱，然後根據路徑將流量導到正確的服務
        - https://app.test/ → 前端
        - https://app.test/submit → 後端  

   5. 這時，我們的 frontend 也就不用寫死後端的 port 了
    
      ```jsx
      function submit() {
        const content = document.getElementById("msg").value;
        // 原本的寫法
        // fetch("http://192.168.49.2:30368/submit", {
        // fetch("http://localhost:8000/submit", {
        fetch("/submit", { //<--- /submit 就會將流量導向後端
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content })
        }).then(r => alert("Sent!"));
      }
      ```
    
      記得改完 index.html 後重新在 minikube 的 docker 中 build Docker image
      
        1. `docker build -t frontend ./frontend`
        2. `kubectl rollout restart deployment frontend`
   
   6. 啟用 Ingress 後，就可以直接在搜尋欄打上 [https://app.test](https://app.test) 而非 ip:port 的格式

       <img width="381" height="165" alt="image (21)" src="https://github.com/user-attachments/assets/1ef7b62b-8627-4aed-81d8-8fa158b9a2e7" />

### HPA

根據 Pod 的資源使用狀況自動調整 Pod 的副本數

1. 啟動 Metrics Server 讓 HPA 可以收集資源使用情況 (CPU / Memory)
   
   `minikube addons enable metrics-server`
   
   `kubectl top pod` 可以看到 pod 的使用情況代表有成功啟動
   
3. 新增 frontend-hpa.yaml
   ```yaml
    apiVersion: autoscaling/v2
    kind: HorizontalPodAutoscaler
    metadata:
      name: frontend-hpa
    spec:
      scaleTargetRef:
        apiVersion: apps/v1
        kind: Deployment
        name: frontend
      minReplicas: 1
      maxReplicas: 5
      metrics:
      - type: Resource
        resource:
          name: cpu
          target:
            type: Utilization
            averageUtilization: 50
   ```
    - 當前端 Deployment 的 平均 CPU 使用率 > 50 %，自動增加 Pod 最多到 5 個
    - 當前端 Deployment 的 平均 CPU 使用率 < 50 %，自動減少 Pod 最少到 1 個

3. frontend-deployment.yaml 加上 pod 對於 CPU 的使用需求
    
    ```yaml
    containers:
      - image: frontend
        imagePullPolicy: Never
        name: frontend
        ports:
          - containerPort: 80
            protocol: TCP
        resources:  
          requests:
            cpu: "100m"  # 一個核心為 1000m，這樣寫代表預期每個 frontend 的 pod 會用到 0.1 個核心
          limits:
            cpu: "500m"  # 表示容器最多能使用 0.5 個 CPU 核心，超過這個限制，Kubernetes 會限制（限速）容器 CPU 使用
    ```

    結合兩個 yaml 的設定，前端的 deployment 平均使用 100m x 50% = 50m = 0.05 核心時就會開始增加 replicas 的數量
    
5. apply hpa 和修改後的前端 deployment
   
   `kubectl apply -f frontend-hpa.yaml`
   `kubectl apply -f frontend-deployment.yaml`

   可以透過 `kubectl get hpa <frontend-pod-name>` 查看運作中的 HPA
   
   <img width="786" height="78" alt="image (22)" src="https://github.com/user-attachments/assets/ff019346-8645-4317-80d4-fb83aeebc58d" />

6. 測試 HPA 功能，我們可以用無限迴圈模擬 CPU 使用率飆升的情況

   1. 建議開啟三個 cmd
   
      - 一個跑 `kubectl get pods -w` 監控 pods 變化  
      - 一個跑 `kubectl get hpa -w` 監控 hpa 變化  
      - 一個 `kubectl exec -it <frontend-pod-name> -- /bin/sh` 進入 pod  
        再用 `while true; do :; done &` 產生無限迴圈
          
      可以看到 hpa 變化，CPU 使用率飆升後 Replicas 最多增加到 5 個  
      
      <img width="730" height="344" alt="image (23)" src="https://github.com/user-attachments/assets/f64d37a5-da30-48be-aa53-cddbd300fd69" />
      
      然後 pod 最多增加到 5 個  
  
      <img width="570" height="284" alt="image (24)" src="https://github.com/user-attachments/assets/1c283d5a-0543-47b9-966f-7edb8b744f04" />
    
   2. 結束後 pod 內執行 `kill %1` 去中止無限迴圈
   3. 過大約五分鐘後，可以看到使用率降低並且 Replicas 只剩下 1
    
      <img width="792" height="129" alt="image (25)" src="https://github.com/user-attachments/assets/62e07642-d7c0-444a-ab18-353dd788df9a" />
    
      然後多執行的 4 個 frontend 的 pod 也自動中止了 ( Terminating → Completed )
      
      <img width="674" height="448" alt="image (26)" src="https://github.com/user-attachments/assets/fa40fbaa-46df-4c94-8a10-9f2f8ce46a12" />


### Rolling Update

可以確保不停止整個服務的情況下，逐步更新舊的 Pod 到新的 Pod，並可在更新異常時回復到之前的狀態

1. 在 backend-deployment.yaml 的 spec 中加上 RollingUpdate
    ```yaml
    replicas: 3
    strategy:             
      type: RollingUpdate
      rollingUpdate:
        maxUnavailable: 1   # 允許最多 1 個不可用的 pod
        maxSurge: 1         # 允許最多可以啟動比 replicas 多 1 個的 Pod
    ```

2. 把 image 改成不存在的名稱 ( `image: backend` -> `image: backend-error` 

3. 開啟一個單獨的終端機執行 `kubectl get pods -w` 監看 pod 變化過程，可以看到原本有 3 個正常 Running 的 backend pod

4. 再次 `kubectl apply -f backend-deployment.yaml`，觀察 Pod 變化過程為

   <img width="649" height="653" alt="image (30)" src="https://github.com/user-attachments/assets/3918f29e-a1b0-41cf-88bc-622d3ec99ad3" />

   1. kubernetes 多啟動 maxSurge 個 pod 作為新版本的 backend (`backend-85989f88d6-bmfq7` 和 `backend-8598f88d6-jjkmq`)，STATUS 變化為 Pending → ContainerCreating
      
   2. kubernetes 終結舊的 maxUnavailable 個 backend pod (`backend-546f6b57-l4tlp`)，狀態從 Terminating 變為 Completed
     
   3. 錯誤的 image 無法抓取，由於我們設定 `restartPolicy: Always`，新啟動的兩個 pod 會一直嘗試拉 image，狀態會無限循環 ErrImagePull → ImagePullBackOff
     
   4. 檢查當前的 pod 可以發現，舊的兩個 pod 還在正常運作中，但會多出兩個狀態異常的 pod
        
      <img width="638" height="204" alt="image (28)" src="https://github.com/user-attachments/assets/71d91373-8c61-4f71-ac5d-49e0b186c53f" />
        
    
5. 發現更新有問題後，我們可以用 `kubectl rollout undo deployment/backend` 回到上一次部屬的版本
    
   （注意：如果上一個版本的 pod 有異常也會回到異常的狀態）
   
   <img width="691" height="629" alt="image (29)" src="https://github.com/user-attachments/assets/157d3248-8bae-447a-aba4-23246aaae73a" />
   
   1. kubernetes 先將本次新增的 pod 終結，STATUS 從 Terminating 變為 ContainerStatusUnknown
   
   2. kubernetes 嘗試根據上一次部屬的 deployment.yaml 建立 pod `backend-546f6b57-xmnjn`，STATUS 從 ContainerCreating 變為 Running  
    
   再次檢查可以看到可用的後端 pod 回到 3 個

   <img width="567" height="183" alt="image (27)" src="https://github.com/user-attachments/assets/a9e36bde-4fcb-43ab-bbbb-5ffa4b846862" />
    
---

最後，照步驟完成後的樣子，以及部屬的流程請參考 [![GitHub Repo](https://img.shields.io/badge/GitHub-Fullstack--K8s--Demo-181717?logo=github)](https://github.com/rena311706015/Fullstack-K8s-Demo)
