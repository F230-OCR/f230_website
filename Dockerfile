#what should i do with this file?
#this file is used to create a docker image
#write the code
FROM python:3.9-alpine
COPY . /app 
WORKDIR /app
RUN pip install -r requirements.txt
CMD python app.py
#save the file
#exit the editor
#build the docker image
#docker build -t flaskapp .
#run the docker image
#docker run -p 5000:5000 flaskapp
#open the browser and type http://localhost:5000
#you will see the output
#to stop the container
#docker ps
#docker stop <container_id>
#to remove the container
#docker ps -a
#docker rm <container_id>
#to remove the image
#docker images
#docker rmi <image_id>
#to remove all the images
#docker rmi $(docker images -q)
#to remove all the containers
#docker rm $(docker ps -a -q)
#to remove all the images and containers
#docker rmi $(docker images -q) -f
#docker rm $(docker ps -a -q) -f
#to remove all the images and containers
#docker system prune -a
#to remove all the images and containers
#docker system prune -a -f
#to remove all the images and containers
#docker system prune -a -f --volumes