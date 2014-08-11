Pootle Template Generator
=========================

This is extension action for Pootle 2.5.1. It can generate
template (POT) files from Pootle's UI.

Installation
------------

0. Get it!

    ```
    cd ~/Devel/
    git clone https://github.com/tchx84/pootle-tg.git
    ```

1. Copy this extention to the proper directory:

    ```
    cp ~/Devel/pootle-tg/template_generator.py /var/www/pootle/env/lib/python2.7/site-packages/pootle/scripts/ext_actions/
    ```

2. Users with administrate permissions should be able to use it from actions section.

Limitations
-----------

* The xgettext call is hardcoded to work python projects. Nothing hard to change though ;)
