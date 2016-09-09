#!/usr/bin/env python

import mistune
import argparse
from sys import argv
from datetime import date
import sqlite3
import flask
import os
import hashlib

app = flask.Flask(__name__)

def create_db():
    if not os.path.exists('txti.db'):
        db = sqlite3.connect('txti.db')
        db.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY, date TEXT NOT NULL, url TEXT NOT NULL, title TEXT NOT NULL, content TEXT NOT NULL, isStatic BOOLEAN NOT NULL, isPublished BOOLEAN NOT NULL)")
        db.execute("CREATE TABLE users (user TEXT NOT NULL, password TEXT NOT NULL)")
        db.execute("INSERT INTO users (user, password) VALUES ('admin', '')")
        db.commit()
        db.close()


@app.route('/')
def render_index():
    db = sqlite3.connect('txti.db')
    c = db.cursor()
    c.execute("SELECT * FROM posts WHERE isStatic = 0 ORDER BY date('date') DESC")
    data = c.fetchall()
    
    posts = []
    for raw in data:
            posts.append({ 'title': raw[3], 'date': raw[1], 'url': raw[2], 'content': raw[4]})

    pages = []
    c.execute("SELECT * FROM posts WHERE isStatic = 1")
    data = c.fetchall()
    for raw in data:
            pages.append({ 'title': raw[3], 'date': raw[1], 'url': raw[2], 'content': raw[4]})

    data = c.fetchall()
    c.close()

    return flask.render_template('index.html',
                           title='Home',
                           posts=posts,
                           pages=pages)


@app.route('/<name>')
def post(name):
    db = sqlite3.connect('txti.db')
    c = db.cursor()
    c.execute("SELECT * FROM posts WHERE url=?", (name,))
    data = c.fetchone()
    c.close()
    renderer = mistune.Renderer(escape=True)
    markdown = mistune.Markdown(renderer=renderer)
    content = markdown(data[4])
    post = { 'title': data[3], 'date': data[1], 'url': data[2], 'content': content }
    return flask.render_template('post.html',
                                post=post)


@app.route('/<name>/edit')
def edit(name):
    db = sqlite3.connect('txti.db')
    c = db.cursor()
    c.execute("SELECT * FROM posts WHERE url=?", (name,))
    data = c.fetchone()
    c.close()
    post = { 'title': data[3], 'date': data[1], 'url': data[2], 'content': data[4] }
    return flask.render_template('edit.html',
                                post=post)


@app.route('/<name>/save', methods=['POST'])
def save(name):
    content = flask.request.form['content']
    db = sqlite3.connect('txti.db')
    c = db.cursor()
    c.execute("UPDATE posts set content=? WHERE url=?", (content, name))
    c.close()
    db.commit()
    return flask.redirect('/'+name)


@app.route('/write', methods=['GET', 'POST'])
def write():
    if flask.request.method == 'GET':
        return flask.render_template('write.html',
                                post=post)

    db = sqlite3.connect('txti.db')
    c = db.cursor()
    date = '2016-09-07'
    url = flask.request.form['url']
    content = flask.request.form['content']
    title = flask.request.form['title']

    if flask.request.form['is_static'] == 'on':
        is_static =  True
    else:
        is_static = False

    #TODO:
    #   add option to save posts not publishing them
    is_published = True

    c.execute("INSERT INTO posts ('date', 'url', 'title', 'content', 'isStatic', 'isPublished') VALUES (?,?,?,?,?,?) ", (date, url, title, content, is_static, is_published))
    c.close()
    db.commit()
    return flask.redirect('/'+url)

@app.route('/<name>/delete', methods=['GET'])
def delete(name):
    db = sqlite3.connect('txti.db')
    c = db.cursor()
    c.execute("DELETE FROM posts WHERE url=?", (name,))
    c.close()
    db.commit()
    return flask.redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if flask.request.method == 'POST':
        db = sqlite3.connect('txti.db')
        c = db.cursor()
        c.execute("SELECT user,password FROM users")
        data = c.fetchone()
        pass_hash = hashlib.md5()
        pass_hash.update(flask.request.form['password'])
        if flask.request.form['username'] == data[0] and pass_hash.hexdigest() == data[1]:
            flask.session['logged_in'] = True
            return flask.redirect('/write')
    return flask.render_template('login.html', error=error)



if __name__ == '__main__':
    create_db()
    app.config.update(SECRET_KEY='development key')
    app.run(host= 'localhost')