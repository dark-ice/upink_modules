<html>
<head>
    <style type="text/css">
        body {
            margin: 0;
            padding: 0;
        }

        .p14 {
            font-size: 8pt;
        }

        .u {
            text-decoration: underline;
        }

        .wrapper {
            position: relative;
            height: 690px;
        }

        .us, .client {
            text-align: center;
            width: 300px;
        }

        .client {
            position: absolute;
            right: 0;
            bottom: 0;
        }
    </style>

</head>
<body>
% for o in objects:
    <div class="wrapper">

        <div class="us">
            <p class="u">ООО "АП Групп"</p>
            <p>ул. Новый Арбат, д. 15</p>
            <p>помещение 1, комната 19</p>
            <p>г. Москва</p>
            <p>119019</p>
        </div>

        <div class='client'>
            <p>${ o.bank_id.fullname or '-' }</p>
            <p>${ get_post_client(o.bank_id.address_ids)[0] or '-'}</p>
            <p>${ get_post_client(o.bank_id.address_ids)[1] or '-'}</p>
            <p>${ get_post_client(o.bank_id.address_ids)[2] or '-'}</p>
        </div>
    </div>
% endfor
</body>
</html>