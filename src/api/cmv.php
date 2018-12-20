<?php
/*
 * cmv-php
 * github.com/01mu
 */

class cmv
{
    private $orders = ['score', 'date', 'comments'];
    private $limits = [50, 100, 250];
    private $sorts = ['asc', 'desc'];
    private $conn;

    public function conn($server, $user, $pw, $db)
    {
        try
        {
            $conn = new PDO("mysql:host=$server;dbname=$db", $user, $pw);
            $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        }
        catch(PDOException $e)
        {
            echo "Error: " . $e->getMessage();
        }

        $this->conn = $conn;
    }

    public function get_posts($limit, $order, $start, $sort)
    {
        $json = array();

        if(!isset($limit) || !isset($order) || !isset($start) || !isset($sort))
        {
            echo json_encode([['Response' => 'Error']]);
            return;
        }

        if(!in_array($limit, $this->limits))
        {
            echo json_encode([['Response' => 'Error']]);
            return;
        }

        if(!in_array($order, $this->orders))
        {
            echo json_encode([['Response' => 'Error']]);
            return;
        }

        if(!in_array($sort, $this->sorts))
        {
            echo json_encode([['Response' => 'Error']]);
            return;
        }

        if(!is_numeric($start))
        {
            echo json_encode([['Response' => 'Error']]);
            return;
        }

        $query = 'SELECT title, op, url, comments, delta, ' .
            'score, date, last_update ' .
            'FROM posts ORDER by :order :sort LIMIT :a OFFSET :b';

        $stmt = $this->conn->prepare($query);

        $stmt->bindParam(':order', $order, PDO::PARAM_STR);
        $stmt->bindParam(':sort', $sort, PDO::PARAM_STR);
        $stmt->bindParam(':a', $limit, PDO::PARAM_INT);
        $stmt->bindParam(':b', $start, PDO::PARAM_INT);

        $stmt->execute();

        while($row = $stmt->fetch())
        {
            $json[] = ['title' => $row['title'],
                'op' => $row['op'],
                'url' => $row['url'],
                'comments' => $row['comments'],
                'delta' => $row['delta'],
                'score' => $row['score'],
                'last_update' => $this->time($row['last_update']),
                'date' => $this->time($row['date'])];
        }

        $this->show_json($json);
    }

    public function search_posts($limit, $search, $start)
    {
        $json = array();

        if(!isset($limit) || !isset($search) || !isset($start))
        {
            echo json_encode([['Response' => 'Error']]);
            return;
        }

        if(!in_array($limit, $this->limits))
        {
            echo json_encode([['Response' => 'Error']]);
            return;
        }

        $search = '%' . $search . '%';

        $query = 'SELECT DISTINCT title, op, url, comments, delta, score, ' .
            'date FROM posts WHERE op LIKE :c OR title LIKE :d ' .
            'ORDER by score LIMIT :a OFFSET :b';

        $stmt = $this->conn->prepare($query);

        $stmt->bindParam(':c', $search, PDO::PARAM_STR);
        $stmt->bindParam(':d', $search, PDO::PARAM_STR);
        $stmt->bindParam(':a', $limit, PDO::PARAM_INT);
        $stmt->bindParam(':b', $start, PDO::PARAM_INT);

        $stmt->execute();

        while($row = $stmt->fetch())
        {
            $json[] = ['title' => $row['title'],
                'op' => $row['op'],
                'url' => $row['url'],
                'comments' => $row['comments'],
                'delta' => $row['delta'],
                'score' => $row['score'],
                'date' => $this->time($row['date'])];
        }

        $this->show_json($json);
    }

    public function single($id)
    {
        $json = array();
        $found = 0;

        if(!isset($id))
        {
            echo json_encode([['Response' => 'Error']]);
            return;
        }

        $query = 'SELECT * FROM posts WHERE id = :id';

        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(":id", $id);
        $stmt->execute();

        while($row = $stmt->fetch())
        {
            $found = 1;

            $json[] = ['title' => $row['title'],
                'op' => $row['op'],
                'url' => $row['url'],
                'comments' => $row['comments'],
                'delta' => $row['delta'],
                'score' => $row['score'],
                'last_update' => $this->time($row['last_update']),
                'date' => $this->time($row['date'])];
        }

        if($found == 0)
        {
            echo json_encode([['Response' => 'Error']]);
            return;
        }
        else
        {
            $this->show_json($json);
        }
    }

    private function show_json($json)
    {
        if(count($json) == 0)
        {
           echo json_encode([['Response' => 'Empty']]);
        }
        else
        {
            $end = array();

            $end[0] = ['Response' => 'Good'];
            $end[1] = $json;
            $end[2] = $this->stats($db);

            echo json_encode($end);
        }
    }

    private function stats()
    {
        $json = array();
        $chk = ['first_update', 'last_update'];

        $query = 'SELECT * FROM stats';
        $result = $this->conn->query($query);

        foreach($result as $row)
        {
            if(in_array($row['input'], $chk))
            {
                $row['value'] = $this->time($row['value']);
            }

            $json[] = ['value' => $row['value'], 'input' => $row['input']];
        }

        return $json;
    }

    private function time($datetime, $full = false)
    {
        $datetime = '@' . $datetime;

        $now = new DateTime;
        $ago = new DateTime($datetime);
        $diff = $now->diff($ago);

        $diff->w = floor($diff->d / 7);
        $diff->d -= $diff->w * 7;

        $string = array(
            'y' => 'year',
            'm' => 'month',
            'w' => 'week',
            'd' => 'day',
            'h' => 'hour',
            'i' => 'minute',
            's' => 'second',
        );

        foreach ($string as $k => &$v)
        {
            if($diff->$k)
            {
                $v = $diff->$k . ' ' . $v . ($diff->$k > 1 ? 's' : '');
            }
            else
            {
                unset($string[$k]);
            }
        }

        if(!$full)
        {
            $string = array_slice($string, 0, 1);
        }

        return $string ? implode(', ', $string) . ' ago' : 'just now';
    }
}
